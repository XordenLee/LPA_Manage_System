from django.contrib import admin

from LPAapp.models import Branch, Commodity, Person, Number, Quarter

admin.site.register(Commodity)
admin.site.register(Branch)
admin.site.register(Person)
admin.site.register(Quarter)
admin.site.register(Number)