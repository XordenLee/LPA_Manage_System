from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, FileResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission, User
from django.contrib.auth import login, logout, authenticate

from .models import Branch, Commodity, Person, Number, Quarter
from .forms import BranchForm, PersonForm, CommodityForm, NumberForm, QuarterForm

import shutil, os
import xlrd, xlwt
import zipfile
import xml.etree.cElementTree as ET

more = 2.0

def index(request):
    quarter = None
    if Quarter.objects.filter(current=True).exists():
        quarter = Quarter.objects.get(current=True)
    if request.method == 'GET':
        return render(request, 'LPAapp/index.html', {'quarter':quarter})
    username = request.POST.get('username','')
    password = request.POST.get('password','')
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse('LPAapp:index'))
    else:
        content = {'quarter':quarter, 'username':username, 'password':password}
        return render(request, 'LPAapp/index.html', content)

def getlis(quarter, persons):
    lis = []
    end1 = [0] * len(persons)
    end2 = [0] * len(persons)
    for co in Commodity.objects.filter(quarter=quarter).all():
        tem = []
        tem.append(str(co.proname) + ' ¥' + str(co.price))
        t_total = 0
        j = 1
        for person in persons:
            number = co.number_set.filter(person=person).first()
            if number == None:
                tem.append('')
                j += 1
                continue
            tem.append(str(number.value))
            t_total += number.value
            end1[j - 1] += number.value
            end2[j - 1] += float(number.value) * float(co.price)
            j += 1
        m_total = float(t_total) * float(co.price)
        tem.append(str(t_total))
        tem.append(str(round(m_total, 2)))
        lis.append(tem)
    t1 = 0
    t2 = 0
    t3 = 0
    end3 = []
    for pe in persons:
        end3.append(pe.limit)
    for k in range(len(persons)):
        t1 += end1[k]
        t2 += end2[k]
        t3 += end3[k]
    tem = []
    tem.append('个数合计')
    for e1 in end1:
        tem.append(str(e1))
    tem.append(str(t1))
    tem.append('')
    lis.append(tem)
    tem = []
    tem.append('金额合计')
    for e2 in end2:
        tem.append(str(round(e2, 2)))
    tem.append('')
    tem.append(str(round(t2, 2)))
    lis.append(tem)
    redl = []
    tem = []
    tem.append('个人限额')
    for k in range(len(end3)):
        tem.append(str(round(end3[k], 2)))
        if float(end3[k]) - float(end2[k]) > 10.0:
            redl.append(k + 1)
    tem.append('')
    tem.append(str(round(t3, 2)))
    lis.append(tem)
    return [lis, redl]

def savelis(persons, lis0, union_name):
    lis = lis0[0]
    redl = lis0[1]
    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('sheet1')
    worksheet.col(0).width = 256 * 50
    al = xlwt.Alignment()
    al.horz = 0x02
    al.vert = 0x01
    font = xlwt.Font()
    font.height = 320
    style = xlwt.XFStyle()
    style.alignment = al
    style.font = font
    worksheet.write_merge(0, 1, 0, len(persons) + 2, union_name, style)
    font_bold = xlwt.Font()
    font_bold.bold = True
    style_bold = xlwt.XFStyle()
    style_bold.font = font_bold
    font_red = xlwt.Font()
    font_red.colour_index = 2
    style_red = xlwt.XFStyle()
    style_red.font = font_red
    worksheet.write(2, 0, '货品名称', style_bold)
    i = 1
    for tb in persons:
        worksheet.write(2, i, tb.name, style_bold)
        i += 1
    worksheet.write(2, i, '个数合计', style_bold)
    worksheet.write(2, i + 1, '金额合计', style_bold)
    for m in range(len(lis)):
        for n in range(len(lis[0])):
            if n in redl:
                worksheet.write(m + 3, n, lis[m][n], style_red)
            else:
                worksheet.write(m + 3, n, lis[m][n])
    fname = union_name + '.xls'
    workbook.save('media/export/' + fname)

@login_required
@permission_required('LPAapp.view_branch')
def branches(request):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    if request.user.has_perm('auth.view_user'):
        branches = Branch.objects.filter(quarter=quarter).order_by('id')
    else:
        for p in request.user.person_set.all():
            if p.branch.quarter == quarter:
                branches = [p.branch]
                break
    if request.method == 'POST':
        check_list = request.POST.getlist('checkItem')
        if len(check_list) == 0:
            return HttpResponseRedirect(reverse('LPAapp:branches'))
        persons = []
        union_name = quarter.text
        for id in check_list:
            branch = Branch.objects.get(id=int(id))
            union_name += '-'+branch.text
            persons += list(branch.person_set.all())
        lis0 = getlis(quarter, persons)
        savelis(persons, lis0, union_name)
        fname = union_name + '.xls'
        file = open('media/export/' + fname, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        dispo = 'attachment;filename="{0}"'.format(fname)
        response['Content-Disposition'] = dispo.encode('gbk')
        return response

    context = {'branches':branches, 'quarter':quarter}
    return render(request, 'LPAapp/branches.html', context)

@login_required
@permission_required('LPAapp.view_number')
def person(request):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    person = None
    for p in request.user.person_set.all():
        if p.branch.quarter == quarter:
            person = p
            break
    if person == None:
        return HttpResponseRedirect(reverse('LPAapp:persons'))

    if request.method == 'POST':
        proid = int(request.POST.get('proid', ''))
        count = int(request.POST.get('count', ''))
        remark = request.POST.get('remark', '')
        commodity = Commodity.objects.get(proid=proid)
        increment = float(count) * float(commodity.price)
        new_value = float(person.value) + increment
        if new_value > float(person.limit) + more:
            return HttpResponseRedirect(reverse('LPAapp:person'))
        new_number = Number(person=person,commodity=commodity,value=count,remark=remark)
        new_number.save()
        person.value = new_value
        person.save()
        return HttpResponseRedirect(reverse('LPAapp:person'))

    numbers = []
    sc = []
    total = 0.0
    if Number.objects.filter(person=person).exists():
        for n in person.number_set.all():
            sc.append(int(n.commodity.proid))
            total += float(n.value) * float(n.commodity.price)
        if float(person.value) != total:
            person.value = round(total, 2)
            person.save()
        sc.sort()
        for c in sc:
            for n in person.number_set.all():
                if int(n.commodity.proid) == c:
                    numbers.append(n)
    rest = 0.00
    if float(person.value) < float(person.limit):
        rest = round(float(person.limit) - float(person.value), 2)
    commodities = []
    for co in Commodity.objects.filter(quarter=quarter).order_by('id'):
        commodities.append(co)
    for nu in person.number_set.all():
        if nu.commodity in commodities:
            commodities.remove(nu.commodity)
    context = {'person': person, 'numbers':numbers, 'quarter':quarter, 'commodities': commodities, 'rest': rest, 'more':more}
    # if request.user.has_perm('auth.view_group'):
    #     return render(request, 'LPAapp/person_perm.html', context)
    return render(request, 'LPAapp/person.html', context)

@login_required
@permission_required('LPAapp.view_number')
def person_view(request, person_id):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    if not Person.objects.filter(id=person_id).exists():
        return HttpResponseRedirect(reverse('LPAapp:persons'))
    person = Person.objects.get(id=person_id)
    numbers = []
    sc = []
    total = 0.0
    if Number.objects.filter(person=person).exists():
        for n in person.number_set.all():
            sc.append(n.commodity.proid)
            total += float(n.value) * float(n.commodity.price)
        if float(person.value) != total:
            person.value = round(total, 2)
            person.save()
        sc.sort()
        for c in sc:
            for n in person.number_set.all():
                if n.commodity.proid == c:
                    numbers.append(n)
    context = {'person': person, 'numbers':numbers, 'quarter':quarter}
    return render(request, 'LPAapp/person_view.html', context)

@login_required
@permission_required('LPAapp.view_commodity')
def commodities(request):
    def GetImgDic(relfile, docfile):
        r = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

        tree1 = ET.parse(relfile)
        root = tree1.getroot()
        id_img = {}
        for child in root:
            id_img[child.attrib['Id']] = child.attrib['Target']

        tree2 = ET.parse(docfile)
        root2 = tree2.getroot()
        num_img = {}
        for c in root2:
            co = c[0][2].text
            do = c[2][1][0].attrib[r + 'embed']
            num_img[co] = id_img[do]
        return num_img

    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    if request.method == 'POST':
        if not 'file' in request.FILES:
            return HttpResponseRedirect(reverse('LPAapp:commodities'))
        f = request.FILES['file']
        extend = os.path.splitext(f.name)[1]
        if extend != '.xlsx' and extend != '.xls':
            return HttpResponseRedirect(reverse('LPAapp:commodities'))
        with open(f.name, 'wb') as de:
            for chunk in f.chunks():
                de.write(chunk)

        basen = f.name.split('.')[0]
        new_name = basen + '.zip'
        if os.path.exists(new_name):
            os.remove(new_name)
        os.rename(f.name, new_name)
        file_zip = zipfile.ZipFile(new_name, 'r')
        for files in file_zip.namelist():
            file_zip.extract(files, basen)
        file_zip.close()
        os.rename(new_name, f.name)
        num_img = {}
        if os.path.exists(basen + '/xl/drawings/_rels/drawing1.xml.rels'):
            num_img = GetImgDic(basen + '/xl/drawings/_rels/drawing1.xml.rels', basen + '/xl/drawings/drawing1.xml')
        wb = xlrd.open_workbook(f.name)
        table = wb.sheets()[0]
        nrows = table.nrows
        if not os.path.exists('media/img/'+str(quarter.id)):
            os.mkdir('media/img/'+str(quarter.id))
            shutil.copy('media/img/0x7xv9db3.jpg','media/img/'+str(quarter.id)+'/0x7xv9db3.jpg')
        for i in range(1, nrows):
            lis = table.row_values(i)
            if type(lis[0]) == str:
                if Commodity.objects.filter(quarter=quarter, proid=int(lis[0])).exists():
                    continue
                new_commodity = Commodity(proid=int(lis[0]),proname=lis[1],price=lis[2],quarter=quarter)
                new_commodity.save()
                if str(i) in num_img:
                    shutil.copy(basen+'/xl'+num_img[str(i)][2:], 'media/img/'+str(quarter.id)+'/'+lis[0].strip()+'.jpg')
                    new_commodity.proimg.name = 'img/'+str(quarter.id)+'/' + lis[0].strip() + '.jpg'
                    new_commodity.save()
            else:
                if Commodity.objects.filter(quarter=quarter, proid=int(lis[0])).exists():
                    continue
                new_commodity = Commodity(proid=int(lis[0]),proname=lis[1],price=lis[2],quarter=quarter)
                new_commodity.save()
                if str(i) in num_img:
                    shutil.copy(basen+'/xl'+num_img[str(i)][2:], 'media/img/'+str(quarter.id)+'/'+str(int(lis[0])).strip()+'.jpg')
                    new_commodity.proimg.name = 'img/'+str(quarter.id)+'/' + str(int(lis[0])).strip() + '.jpg'
                    new_commodity.save()
        os.remove(f.name)
        shutil.rmtree(basen)
        return HttpResponseRedirect(reverse('LPAapp:commodities'))

    commodities = Commodity.objects.filter(quarter=quarter).order_by('id')
    context = {'commodities':commodities, 'quarter':quarter}
    return render(request, 'LPAapp/commodities.html', context)

@login_required
def download_commodities(request):
    if not os.path.exists('media/import/commodities.xlsx'):
        return
    file = open('media/import/commodities.xlsx', 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    dispo = 'attachment;filename="{0}"'.format('commodities.xlsx')
    response['Content-Disposition'] = dispo
    return response

@login_required
@permission_required('LPAapp.view_person')
def persons(request):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    if request.method == 'POST':
        if not 'file' in request.FILES:
            return HttpResponseRedirect(reverse('LPAapp:persons'))
        f = request.FILES['file']
        wb = xlrd.open_workbook(filename=None, file_contents=f.read())
        table = wb.sheets()[0]
        nrows = table.nrows
        for i in range(1, nrows):
            lis = table.row_values(i)
            if len(lis)<5:
                continue
            if not Branch.objects.filter(quarter=quarter, text=lis[0]).exists():
                new_branch = Branch(quarter=quarter, text=lis[0])
                new_branch.save()
            branch = Branch.objects.get(quarter=quarter, text=lis[0])
            if Person.objects.filter(branch=branch, name=lis[1].replace(' ','')).exists():
                continue
            if not User.objects.filter(username=lis[1].replace(' ','')).exists():
                user = User.objects.create_user(username=lis[1].replace(' ',''), password='fiprs123456')
                group = Group.objects.get(name='employee')
                user.groups.add(group)
                if lis[3] == '1':
                    group1 = Group.objects.get(name='viewer')
                    user.groups.add(group1)
                if lis[4] == '1':
                    group2 = Group.objects.get(name='leader')
                    user.groups.add(group2)
            user1 = User.objects.get(username=lis[1].replace(' ',''))
            new_person = Person(user=user1, branch=branch, name=lis[1].replace(' ',''), value=0.00, limit=lis[2])
            new_person.save()
    if request.user.has_perm('auth.view_user'):
        persons = Person.objects.all()
    else:
        for p in request.user.person_set.all():
            if p.branch.quarter == quarter:
                persons = p.branch.person_set.all()
                break
    context = {'quarter':quarter, 'persons':persons}
    return render(request, 'LPAapp/persons.html', context)

@login_required
@permission_required('LPAapp.view_quarter')
def quarters(request):
    current = None
    if Quarter.objects.filter(current=True).exists():
        current = Quarter.objects.get(current=True)
    quarters = Quarter.objects.order_by('id')
    context = {'quarters':quarters, 'current':current}
    return render(request, 'LPAapp/quarters.html', context)

@login_required
@permission_required('LPAapp.view_branch')
def quarter_stat(request, quarter_id):
    current = Quarter.objects.get(current=True)
    quarter = Quarter.objects.get(id=quarter_id)
    branches = Branch.objects.filter(quarter=quarter).order_by('id')
    lis = []
    end1 = [0] * branches.count()
    end2 = [0] * branches.count()
    for co in Commodity.objects.filter(quarter=quarter).all():
        tem = []
        tem.append(str(co.proname) + ' ¥' + str(co.price))
        t_total = 0
        i = 0
        for branch in branches:
            ct = 0
            for p in branch.person_set.all():
                number = co.number_set.filter(person=p).first()
                if number != None:
                    ct += number.value
            if ct == 0:
                tem.append('')
                i += 1
                continue
            tem.append(str(ct))
            t_total += ct
            end1[i] += ct
            end2[i] += float(ct) * float(co.price)
            i += 1
        m_total = float(t_total) * float(co.price)
        tem.append(str(t_total))
        tem.append(str(round(m_total, 2)))
        lis.append(tem)
    t1 = 0
    t2 = 0
    t3 = 0
    end3 = []
    for branch in branches:
        lim = 0
        for p in branch.person_set.all():
            lim += p.limit
        end3.append(lim)
    for k in range(len(end1)):
        t1 += end1[k]
        t2 += end2[k]
        t3 += end3[k]
    tem = []
    tem.append('个数合计')
    for e1 in end1:
        tem.append(str(e1))
    tem.append(str(t1))
    tem.append('')
    lis.append(tem)
    tem = []
    tem.append('金额合计')
    for e2 in end2:
        tem.append(str(round(e2, 2)))
    tem.append('')
    tem.append(str(round(t2, 2)))
    lis.append(tem)
    redl = []
    tem = []
    tem.append('限额合计')
    for k in range(len(end3)):
        tem.append(str(round(end3[k], 2)))
        if float(end3[k]) - float(end2[k]) > branches[k].person_set.count():
            redl.append(k + 1)
    tem.append('')
    tem.append(str(round(t3, 2)))
    lis.append(tem)

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('quarter')
    worksheet.col(0).width = 256 * 50
    al = xlwt.Alignment()
    al.horz = 0x02
    al.vert = 0x01
    font = xlwt.Font()
    font.height = 320
    style = xlwt.XFStyle()
    style.alignment = al
    style.font = font
    worksheet.write_merge(0, 1, 0, branches.count() + 3, quarter.text, style)
    font_bold = xlwt.Font()
    font_bold.bold = True
    style_bold = xlwt.XFStyle()
    style_bold.font = font_bold
    font_red = xlwt.Font()
    font_red.colour_index = 2
    style_red = xlwt.XFStyle()
    style_red.font = font_red
    worksheet.write(2, 0, '货品名称', style_bold)
    i = 1
    for tb in branches:
        worksheet.write(2, i, tb.text, style_bold)
        i += 1
    worksheet.write(2, i, '个数合计', style_bold)
    worksheet.write(2, i + 1, '金额合计', style_bold)
    for m in range(len(lis)):
        for n in range(len(lis[0])):
            if n in redl:
                worksheet.write(m + 3, n, lis[m][n], style_red)
            else:
                worksheet.write(m + 3, n, lis[m][n])
    fname = quarter.text + '.xls'
    workbook.save('media/export/' + fname)

    context = {'branches':branches, 'quarter':quarter, 'lis':lis, 'current':current}
    return render(request, 'LPAapp/quarter_stat.html', context)

@login_required
@permission_required('LPAapp.view_branch')
def quarter_download(request, quarter_id):
    quarter = Quarter.objects.get(id=quarter_id)
    fname = quarter.text + '.xls'
    file = open('media/export/' + fname, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    dispo = 'attachment;filename="{0}"'.format(fname)
    response['Content-Disposition'] = dispo.encode('gbk')
    return response

@login_required
@permission_required('LPAapp.view_branch')
def branch_stat(request, branch_id):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    branch = Branch.objects.get(id=branch_id)
    persons = Person.objects.filter(branch=branch).order_by('id')
    union_name = quarter.text + '-' + branch.text
    lis0 = getlis(quarter, persons)
    lis = lis0[0]
    savelis(persons, lis0, union_name)
    context = {'persons':persons, 'quarter':quarter, 'lis':lis, 'branch':branch}
    return render(request, 'LPAapp/branch_stat.html', context)

@login_required
@permission_required('LPAapp.view_branch')
def branch_download(request, branch_id):
    quarter = Quarter.objects.get(current=True)
    branch = Branch.objects.get(id=branch_id)
    fname = quarter.text + '-' + branch.text + '.xls'
    file = open('media/export/' + fname, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    dispo = 'attachment;filename="{0}"'.format(fname)
    response['Content-Disposition'] = dispo.encode('gbk')
    return response

@login_required
@permission_required('LPAapp.view_branch')
def list_download(request, branch_id):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    branch = Branch.objects.get(id=branch_id)
    pers = Person.objects.filter(branch=branch)
    persons = []
    for person in pers:
        if person.number_set.count() != 0:
            persons.append(person)

    workbook = xlwt.Workbook()
    worksheet = workbook.add_sheet('list')

    alignment = xlwt.Alignment()
    alignment.horz = xlwt.Alignment.HORZ_CENTER
    alignment1 = xlwt.Alignment()
    alignment1.wrap = 1

    borders = xlwt.Borders()
    borders.left = 1
    borders.right = 1
    borders.top = 1
    borders.bottom = 1

    font = xlwt.Font()
    font.name = '宋体'
    font.height = 220
    style = xlwt.XFStyle()
    style.font = font
    style.alignment = alignment1
    style.borders = borders

    style1 = xlwt.XFStyle()
    style1.font = font
    style1.alignment = alignment
    style1.borders = borders

    font_bold = xlwt.Font()
    font_bold.name = '宋体'
    font_bold.height = 220
    font_bold.bold = True
    style_bold = xlwt.XFStyle()
    style_bold.font = font_bold
    style_bold.borders = borders

    style_bold1 = xlwt.XFStyle()
    style_bold1.font = font_bold
    style_bold1.alignment = alignment
    style_bold1.borders = borders

    for i in range(len(persons)):
        person = persons[i]
        worksheet.col(i * 2).width = 256 * 59
        worksheet.write(0, i * 2, '货品名称', style_bold)
        worksheet.write(0, i * 2 + 1, person.name, style_bold1)
        numbers = []
        sc = []
        for n in person.number_set.all():
            sc.append(n.commodity.proid)
        sc.sort()
        for c in sc:
            for n in person.number_set.all():
                if n.commodity.proid == c:
                    numbers.append(n)
        for j in range(len(numbers)):
            worksheet.write(j + 1, i * 2, numbers[j].commodity.proname+' ¥'+str(numbers[j].commodity.price), style)
            worksheet.write(j + 1, i * 2 + 1, str(numbers[j].value), style1)
        worksheet.write(len(numbers) + 1, i * 2, '总计', style)
        worksheet.write(len(numbers) + 1, i * 2 + 1, str(person.value), style1)

    fname = quarter.text + '-' + branch.text + '-个人清单.xls'
    workbook.save('media/export/' + fname)
    file = open('media/export/' + fname, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    dispo = 'attachment;filename="{0}"'.format(fname)
    response['Content-Disposition'] = dispo.encode('gbk')
    return response

@login_required
@permission_required('LPAapp.add_branch')
def new_branch(request):
    quarter = Quarter.objects.get(current=True)
    if request.method != 'POST':
        form = BranchForm()
    else:
        form = BranchForm(request.POST)
        if form.is_valid():
            new_branch = form.save(commit=False)
            new_branch.quarter = quarter
            new_branch.save()
            return HttpResponseRedirect(reverse('LPAapp:branches'))

    context = {'form': form, 'quarter':quarter}
    return render(request, 'LPAapp/new_branch.html', context)

@login_required
@permission_required('LPAapp.add_person')
def new_person(request):
    quarter = Quarter.objects.get(current=True)
    if request.method != 'POST':
        form = PersonForm()
    else:
        form = PersonForm(data=request.POST)
        if form.is_valid():
            new_person = form.save(commit=False)
            if not User.objects.filter(username=new_person.name).exists():
                user = User.objects.create_user(username=new_person.name, password='fiprs123456')
                group = Group.objects.get(name='employee')
                user.groups.add(group)
            user1 = User.objects.get(username=new_person.name)
            new_person.user = user1
            new_person.save()
            return HttpResponseRedirect(reverse('LPAapp:persons'))

    context = {'form':form, 'quarter':quarter}
    return render(request, 'LPAapp/new_person.html', context)

@login_required
@permission_required('LPAapp.add_commodity')
def new_commodity(request):
    quarter = Quarter.objects.get(current=True)
    if request.method != 'POST':
        form = CommodityForm()
    else:
        form = CommodityForm(request.POST, request.FILES)
        if form.is_valid():
            new_commodity = form.save()
            new_commodity.quarter = quarter
            name = new_commodity.proimg.name
            if name != 'img/0x7xv9db3.jpg':
                initial_path = new_commodity.proimg.path
                new_commodity.proimg.name = 'img/'+str(quarter.id)+'/'+new_commodity.proid+'.jpg'
                new_path = os.path.dirname(initial_path)+'\\'+str(quarter.id)+'\\'+new_commodity.proid+'.jpg'
                os.rename(initial_path, new_path)
                new_commodity.save()
            return HttpResponseRedirect(reverse('LPAapp:commodities'))

    context = {'form':form, 'quarter':quarter}
    return render(request, 'LPAapp/new_commodity.html', context)

@login_required
@permission_required('LPAapp.add_quarter')
def new_quarter(request):
    if request.method != 'POST':
        form = QuarterForm()
    else:
        form = QuarterForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('LPAapp:quarters'))

    context = {'form': form}
    return render(request, 'LPAapp/new_quarter.html', context)

@login_required
@permission_required('LPAapp.change_branch')
def edit_branch(request, branch_id):
    branch = Branch.objects.get(id=branch_id)
    if request.method != 'POST':
        form = BranchForm(instance=branch)
    else:
        form = BranchForm(instance=branch, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('LPAapp:branches'))

    context = {'branch':branch, 'form':form}
    return render(request, 'LPAapp/edit_branch.html', context)

@login_required
@permission_required('LPAapp.change_person')
def edit_person(request, person_id):
    quarter = Quarter.objects.get(current=True)
    person = Person.objects.get(id=person_id)

    if request.method != 'POST':
        form = PersonForm(instance=person)
    else:
        form = PersonForm(instance=person, data=request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('LPAapp:persons'))

    context = {'person':person, 'form':form, 'quarter':quarter}
    return render(request, 'LPAapp/edit_person.html', context)

@login_required
@permission_required('LPAapp.change_number')
def edit_number(request, number_id):
    quarter = Quarter.objects.get(current=True)
    number = Number.objects.get(id=number_id)
    value = float(number.value)
    person = number.person

    if request.method == 'POST':
        count = float(request.POST.get('count', ''))
        remark = request.POST.get('remark', '')
        newcreace = (count-value) * float(number.commodity.price)
        newtotal = float(person.value) + newcreace
        if newtotal > float(person.limit) + more:
            return HttpResponseRedirect(reverse('LPAapp:edit_number', args=[number_id]))
        person.value = newtotal
        person.save()
        number.value = count
        number.remark = remark
        number.save()
        return HttpResponseRedirect(reverse('LPAapp:person'))

    context = {'number':number, 'person':person, 'quarter':quarter, 'more':more}
    return render(request, 'LPAapp/edit_number.html', context)

@login_required
@permission_required('LPAapp.change_commodity')
def edit_commodity(request, commodity_id):
    commodity = Commodity.objects.get(id=commodity_id)

    if request.method != 'POST':
        form = CommodityForm(instance=commodity)
    else:
        form = CommodityForm(request.POST, request.FILES, instance=commodity)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('LPAapp:commodities'))

    context = {'commodity':commodity, 'form':form}
    return render(request, 'LPAapp/edit_commodity.html', context)

@login_required
@permission_required('LPAapp.change_quarter')
def edit_quarter(request, quarter_id):
    quarter = Quarter.objects.get(id=quarter_id)
    if request.method != 'POST':
        form = QuarterForm(instance=quarter)
    else:
        form = QuarterForm(data=request.POST, instance=quarter)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('LPAapp:quarters'))

    context = {'quarter':quarter, 'form':form}
    return render(request, 'LPAapp/edit_quarter.html', context)

@login_required
@permission_required('LPAapp.delete_branch')
def delete_branch(request, branch_id):
    branch = Branch.objects.get(id=branch_id)
    branch.delete()
    return HttpResponseRedirect(reverse('LPAapp:branches'))

@login_required
@permission_required('LPAapp.delete_person')
def delete_person(request, person_id):
    person = Person.objects.get(id=person_id)
    person.delete()
    return HttpResponseRedirect(reverse('LPAapp:persons'))

@login_required
@permission_required('LPAapp.delete_number')
def delete_number(request, number_id):
    number = Number.objects.get(id=number_id)
    person = number.person
    decreace = float(number.value) * float(number.commodity.price)
    minus = float(person.value) - decreace
    person.value = minus
    person.save()
    number.delete()
    if person.number_set.count() == 0:
        person.value = 0
        person.save()
    if person.user != request.user:
        return HttpResponseRedirect(reverse('LPAapp:person_view',args=[person.id]))
    else:
        return HttpResponseRedirect(reverse('LPAapp:person'))

@login_required
@permission_required('LPAapp.delete_commodity')
def delete_commodity(request, commodity_id):
    commodity = Commodity.objects.get(id=commodity_id)
    if os.path.exists(commodity.proimg.path) and commodity.proimg.name != 'img/0x7xv9db3.jpg':
        os.remove(commodity.proimg.path)
    commodity.delete()
    return HttpResponseRedirect(reverse('LPAapp:commodities'))

@login_required
@permission_required('LPAapp.delete_quarter')
def delete_quarter(request, quarter_id):
    quarter = Quarter.objects.get(id=quarter_id)
    quarter.delete()
    if Quarter.objects.count() == 0:
        return HttpResponseRedirect(reverse('LPAapp:index'))
    else:
        return HttpResponseRedirect(reverse('LPAapp:quarters'))

@login_required
@permission_required('LPAapp.add_quarter')
def log_control(request):
    if not Quarter.objects.filter(current=True).exists():
        return HttpResponseRedirect(reverse('LPAapp:quarters'))
    quarter = Quarter.objects.get(current=True)
    if request.method == 'POST':
        year = request.POST.get('year', '')
        month = request.POST.get('month', '')
        day = request.POST.get('day', '')
        hour = request.POST.get('hour', '')
        minute = request.POST.get('minute', '')
        if not (year and month and day and hour and minute):
            return HttpResponseRedirect(reverse('LPAapp:log_control'))
        end_time = year+'/'+month+'/'+day+' '+hour+':'+minute+':00'
        quarter.end_time = end_time
        quarter.save()
        return HttpResponseRedirect(reverse('LPAapp:log_control'))
    context = {'quarter':quarter}
    return render(request, 'LPAapp/log_control.html', context)

@login_required
@permission_required('LPAapp.add_quarter')
def log_end(request):
    quarter = Quarter.objects.get(current=True)
    quarter.end_time = '2000/1/1 00:00:00'
    quarter.save()
    return HttpResponseRedirect(reverse('LPAapp:log_control'))

@login_required
@permission_required('LPAapp.delete_branch')
def clear_branches(request):
    quarter = Quarter.objects.get(current=True)
    for branch in Branch.objects.filter(quarter=quarter).all():
        branch.delete()
    return HttpResponseRedirect(reverse('LPAapp:branches'))

@login_required
@permission_required('LPAapp.delete_person')
def clear_persons(request):
    quarter = Quarter.objects.get(current=True)
    for branch in Branch.objects.filter(quarter=quarter).all():
        for person in Person.objects.filter(branch=branch).all():
            person.delete()
    return HttpResponseRedirect(reverse('LPAapp:persons'))

@login_required
@permission_required('LPAapp.delete_commodity')
def clear_commodities(request):
    quarter = Quarter.objects.get(current=True)
    shutil.rmtree("media/img/"+str(quarter.id))
    for commodity in Commodity.objects.filter(quarter=quarter).all():
        commodity.delete()
    return HttpResponseRedirect(reverse('LPAapp:commodities'))

@login_required
@permission_required('LPAapp.delete_quarter')
def setcur_quarter(request, quarter_id):
    if Quarter.objects.filter(current=True).exists():
        quarter = Quarter.objects.get(current=True)
        quarter.current = False
        quarter.save()
    c_quarter = Quarter.objects.get(id=quarter_id)
    c_quarter.current = True
    c_quarter.save()
    return HttpResponseRedirect(reverse('LPAapp:quarters'))

@login_required
@permission_required('LPAapp.delete_number')
def clear_numbers(request, person_id):
    person = Person.objects.get(id=person_id)
    for number in person.number_set.all():
        number.delete()
    person.value = 0.0
    person.save()
    return HttpResponseRedirect(reverse('LPAapp:person'))
