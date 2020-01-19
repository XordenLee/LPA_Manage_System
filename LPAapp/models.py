from django.db import models
from django.contrib.auth.models import User

class Quarter(models.Model):
    text = models.CharField(max_length=200)
    notice = models.CharField(max_length=800)
    current = models.BooleanField(default=False)
    end_time = models.CharField(max_length=10, default='2000/1/1 00:00:00')

    def __str__(self):
        return self.text

class Commodity(models.Model):
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, default=0)
    proid = models.CharField(max_length=10)
    proname = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    proimg = models.ImageField(upload_to='img', default='img/0x7xv9db3.jpg', blank=True)

    class Meta:
        verbose_name_plural = 'commodities'

    def __str__(self):
        return self.proname

class Branch(models.Model):
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, default=0)
    text = models.CharField(max_length=200)

    class Meta:
        verbose_name_plural = 'branches'

    def __str__(self):
        return self.text

class Person(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=0)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=0)
    name = models.CharField(max_length=100)
    limit = models.DecimalField(max_digits=8, decimal_places=2, default=300.00)
    value = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name

class Number(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE, default=0)
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, default=0)
    value = models.IntegerField(default=1)
    remark = models.CharField(max_length=200, blank=True, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.person.name