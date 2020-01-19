from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.contrib.auth import logout, authenticate

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('LPAapp:index'))

def change_pwd(request):
    if request.method == 'GET':
        return render(request, 'users/change_pwd.html', {'msg':''})
    username = request.user.username
    password0 = request.POST.get('password0', '')
    password1 = request.POST.get('password1', '')
    password2 = request.POST.get('password2', '')
    if password0 == '':
        return render(request, 'users/change_pwd.html', {'msg': '原始密码不能为空！'})
    if password1 == '':
        return render(request, 'users/change_pwd.html', {'msg': '新密码不能为空！'})
    if password2 == '':
        return render(request, 'users/change_pwd.html', {'msg': '重复新密码不能为空！'})
    if password1 != password2:
        return render(request, 'users/change_pwd.html', {'msg': '新密码不一致！'})
    if password0 == password1:
        return render(request, 'users/change_pwd.html', {'msg': '新旧密码不能一样！'})
    user = authenticate(request, username=username, password=password0)
    if user is not None:
        user.set_password(password1)
        user.save()
        return HttpResponseRedirect(reverse('LPAapp:index'))
    else:
        return render(request, 'users/change_pwd.html', {'msg': '原始密码错误！'})