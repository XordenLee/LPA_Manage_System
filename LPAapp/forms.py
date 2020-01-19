from django import forms
from .models import Branch, Person, Commodity, Number, Quarter

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['text']
        labels = {'text':'名称'}

class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['branch', 'name', 'limit']
        labels = {'branch':'部门', 'name':'姓名', 'limit':'限额'}
        widgets = {
            'branch': forms.Select(attrs={'class': 'form-control'}),
        }

class CommodityForm(forms.ModelForm):
    class Meta:
        model = Commodity
        fields = ['proid', 'proname', 'price', 'proimg']
        labels = {'proid':'货品编号', 'proname':'货品名称', 'price':'货品单价', 'proimg':'货品图片'}

class NumberForm(forms.ModelForm):
    class Meta:
        model = Number
        fields = ['value', 'remark']
        labels = {'value':'数量', 'remark':'备注'}


class QuarterForm(forms.ModelForm):
    class Meta:
        model = Quarter
        fields = ['text', 'notice']
        labels = {'text':'项目名称', 'notice':'公告'}
