from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Branch(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    pincode = models.CharField(max_length=10)
    contact_number = models.CharField(max_length=15)
    location_url=models.URLField(null=True)
    email = models.EmailField(blank=True, null=True)
    active = models.BooleanField(default=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    password=models.CharField(max_length=100,null=True)


class Branch_Selected(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    session_key=models.CharField(max_length=100,null=True)

class DiagnosticTest(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()  # can be "About the Test"
    instructions = models.TextField(blank=True, null=True)  # Test Preparation
    price = models.DecimalField(max_digits=8, decimal_places=2)
    sample_type = models.CharField(max_length=100)
    report_time = models.CharField(max_length=100)
    reports_within = models.CharField(max_length=100, blank=True, null=True)
    measures = models.TextField(blank=True, null=True)  # What is being measured
    components = models.TextField(blank=True, null=True)  # List of parameters
    purpose = models.TextField(blank=True, null=True)  # Why This Test
    category = models.CharField(max_length=100, blank=True, null=True)
    interpretations = models.TextField(blank=True, null=True)
    branch=models.ForeignKey(Branch,on_delete=models.CASCADE,null=True)
    views = models.IntegerField(default=0)

class TestFAQ(models.Model):
    test = models.ForeignKey('DiagnosticTest', on_delete=models.CASCADE, related_name='faqs')
    question = models.CharField(max_length=255,null=True)
    answer = models.TextField(null=True)

class TestPackage(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.CharField(max_length=100)  # e.g., Fever, Full Body, Diabetes
    tests = models.ManyToManyField(DiagnosticTest)
    branch=models.ForeignKey(Branch,on_delete=models.CASCADE,null=True)

class Checkup(models.Model):
    title = models.CharField(max_length=150)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    tests = models.ManyToManyField(DiagnosticTest, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    views = models.IntegerField(default=0)

    report_time = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    fasting_required = models.BooleanField(default=False)
    sample_type = models.CharField(max_length=100)
    target_audience = models.CharField(max_length=200, blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)

class tbl_Register(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True)
    password=models.CharField(max_length=100,null=True)

ORDER_STATUS_CHOICES = [
    ('new', 'New'),
    ('sample_collected', 'Sample Collected'),
    ('processing', 'Result Pending'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10)
    address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='new')
    result_file = models.FileField(upload_to='results/', null=True, blank=True),
    branch=models.ForeignKey(Branch,on_delete=models.CASCADE,null=True)



class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_type = models.CharField(max_length=20)  # 'test' or 'checkup'
    item_name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=8, decimal_places=2)


class BlogPost(models.Model):
    title = models.CharField(max_length=200,null=True)
    slug = models.SlugField(unique=True)
    content = models.TextField(null=True)
    image = models.ImageField(upload_to="blog_images/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

