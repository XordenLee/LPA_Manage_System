from django.urls import path
from . import views

urlpatterns = [
    path(r'', views.index, name='index'),
    path(r'commodities/',views.commodities, name='commodities'),
    path(r'download_commodities/',views.download_commodities, name='download_commodities'),
    path(r'persons/',views.persons, name='persons'),
    path(r'quarters/', views.quarters, name='quarters'),
    path(r'branches/',views.branches, name='branches'),
    path(r'person', views.person, name='person'),
    path(r'person_view/(?P<person_id>\d+)', views.person_view, name='person_view'),

    path(r'quarter_stat/(?P<quarter_id>\d+)/',views.quarter_stat,name='quarter_stat'),
    path(r'quarter_download/(?P<quarter_id>\d+)/',views.quarter_download,name='quarter_download'),
    path(r'branch_stat/(?P<branch_id>\d+)/',views.branch_stat, name='branch_stat'),
    path(r'branch_download/(?P<branch_id>\d+)/',views.branch_download, name='branch_download'),
    path(r'list_download/(?P<branch_id>\d+)/',views.list_download, name='list_download'),

    path(r'new_branch/',views.new_branch,name='new_branch'),
    path(r'new_person/',views.new_person,name='new_person'),
    path(r'new_commodity/',views.new_commodity,name='new_commodity'),
    path(r'new_quarter/',views.new_quarter,name='new_quarter'),

    path(r'edit_branch/(?P<branch_id>\d+)/',views.edit_branch,name='edit_branch'),
    path(r'edit_person/(?P<person_id>\d+)/',views.edit_person,name='edit_person'),
    path(r'edit_number/(?P<number_id>\d+)/',views.edit_number,name='edit_number'),
    path(r'edit_commodity/(?P<commodity_id>\d+)/',views.edit_commodity,name='edit_commodity'),
    path(r'edit_quarter/(?P<quarter_id>\d+)/',views.edit_quarter,name='edit_quarter'),

    path(r'delete_branch/(?P<branch_id>\d+)/',views.delete_branch,name='delete_branch'),
    path(r'delete_person/(?P<person_id>\d+)/',views.delete_person,name='delete_person'),
    path(r'delete_number/(?P<number_id>\d+)/', views.delete_number, name='delete_number'),
    path(r'delete_commodity/(?P<commodity_id>\d+)/',views.delete_commodity,name='delete_commodity'),
    path(r'delete_quarter/(?P<quarter_id>\d+)/',views.delete_quarter,name='delete_quarter'),

    path(r'log_control/', views.log_control, name='log_control'),
    path(r'log_end/', views.log_end, name='log_end'),

    path(r'clear_branches/', views.clear_branches, name='clear_branches'),
    path(r'clear_persons/', views.clear_persons, name='clear_persons'),
    path(r'clear_commodities/', views.clear_commodities, name='clear_commodities'),
    path(r'setcur_quarter/(?P<quarter_id>\d+)/',views.setcur_quarter,name='setcur_quarter'),
    path(r'clear_numbers/(?P<person_id>\d+)/', views.clear_numbers, name='clear_numbers'),
]