from datetime import timezone, timedelta, date

from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.core.mail import send_mail
import razorpay
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.http import FileResponse, HttpResponse
from django.contrib.auth.hashers import make_password
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str


# Create your views here.
def index(request):
    branches=Branch.objects.all()
    most_viewed_tests = DiagnosticTest.objects.order_by('-views')[:4]
    most_viewed_checkups = Checkup.objects.order_by('-views')[:4]
    return render(request, 'indexnew.html', {
        'most_viewed_tests': most_viewed_tests,
        'most_viewed_checkups': most_viewed_checkups,
        "branches": branches
    })


def admin_login(request):
    return render(request,"admin_login.html")

def admin_login_check(request):
    if request.method=="POST":
        username=request.POST.get("username")
        password=request.POST.get("password")
        user=authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            return redirect("/Admin_Dashboard/")
        else:
            return redirect("/Admin/")

@login_required
def change_password_view(request):
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if new_password != confirm_password:
            messages.error(request, "New passwords do not match.")
        elif len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, "Password updated successfully. Please log in again.")
            return redirect('Admin')  # or to logout

    return render(request, 'change_password.html')


def LogoutAdmin(request):
    logout(request)
    return redirect("/Admin/")
from django.db.models import Count,Sum
from django.utils import timezone
def Admin_Dashboard(request):
    status_counts = Order.objects.values('status').annotate(count=Count('id'))
    today = timezone.now()
    last_week = today - timedelta(days=6)
    orders_by_date = (
        Order.objects
        .filter(created_at__date__gte=last_week.date())
        .extra({'day': "date(created_at)"})
        .values('day')
        .annotate(count=Count('id'))
        .order_by('day')
    )

    item_counts = (
        OrderItem.objects
        .values('item_type')
        .annotate(count=Count('id'))
    )
    customers=User.objects.filter(is_staff=False).count()
    total_sales = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    today_orders = Order.objects.filter(created_at__date=date.today()).count()

    return render(request, 'Admin_Dashboard.html', {
        'status_counts': status_counts,
        'orders_by_date': orders_by_date,
        'item_counts': item_counts,
        'customers' :customers,
        "total_sales":total_sales,
        "today_orders":today_orders
    })


def test_list(request):
    selected_branch_id = request.GET.get('branch')
    branches = Branch.objects.all()
    if selected_branch_id:
        tests = DiagnosticTest.objects.filter(branch_id=selected_branch_id)
    else:
        tests = DiagnosticTest.objects.all()

    return render(request, 'test_list.html', {
        'tests': tests,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
    })

def test_create(request):
    branches=Branch.objects.all()
    if request.method == 'POST':
        test = DiagnosticTest.objects.create(
            name=request.POST['name'],
            description=request.POST['description'],
            instructions=request.POST.get('instructions', ''),
            price=request.POST['price'],
            sample_type=request.POST['sample_type'],
            report_time=request.POST['report_time'],
            reports_within=request.POST.get('reports_within', ''),
            measures=request.POST.get('measures', ''),
            components=request.POST.get('components', ''),
            purpose=request.POST.get('purpose', ''),
            interpretations=request.POST.get('interpretations', ''),
            category=request.POST.get('category', ''),
            branch_id=request.POST.get("branch")
        )

        # 2. Loop through dynamic FAQ inputs and save them
        i = 0
        while True:
            question = request.POST.get(f'faq_question_{i}')
            answer = request.POST.get(f'faq_answer_{i}')
            if question and answer:
                TestFAQ.objects.create(test=test, question=question, answer=answer)
                i += 1
            else:
                break

        return redirect('test_list')

    return render(request, 'test_create.html',{"branches":branches})


def test_edit(request, pk):
    test = get_object_or_404(DiagnosticTest, pk=pk)
    branches=Branch.objects.all()

    if request.method == 'POST':
        # Update test fields
        test.name = request.POST['name']
        test.description = request.POST['description']
        test.instructions = request.POST.get('instructions', '')
        test.price = request.POST['price']
        test.sample_type = request.POST['sample_type']
        test.report_time = request.POST['report_time']
        test.reports_within = request.POST.get('reports_within', '')
        test.measures = request.POST.get('measures', '')
        test.components = request.POST.get('components', '')
        test.purpose = request.POST.get('purpose', '')
        test.interpretations = request.POST.get('interpretations', '')
        test.category = request.POST.get('category', '')
        test.branch_id=request.POST.get("branch")
        test.fasting_required = True if request.POST.get('fasting_required') == 'on' else False
        test.save()

        # Process FAQ updates and additions
        i = 0
        while True:
            question = request.POST.get(f'faq_question_{i}')
            answer = request.POST.get(f'faq_answer_{i}')
            faq_id = request.POST.get(f'faq_id_{i}')

            if question and answer:
                if faq_id:  # Existing FAQ – update
                    try:
                        faq = TestFAQ.objects.get(id=faq_id, test=test)
                        faq.question = question
                        faq.answer = answer
                        faq.save()
                    except TestFAQ.DoesNotExist:
                        pass  # skip if the FAQ doesn't belong to this test
                else:  # New FAQ – create
                    TestFAQ.objects.create(test=test, question=question, answer=answer)
                i += 1
            else:
                break

        return redirect('test_list')

    return render(request, 'test_edit.html', {"test": test,"branches":branches, 'selected_branch_id': test.branch_id })
def test_delete(request, pk):
    test = get_object_or_404(DiagnosticTest, pk=pk)
    test.delete()
    return redirect('test_list')


def package_list(request):
    selected_branch_id = request.GET.get('branch')
    branches = Branch.objects.all()
    if selected_branch_id:
        packages = TestPackage.objects.filter(branch_id=selected_branch_id)
    else:
        packages = TestPackage.objects.all()

    return render(request, 'package_list.html', {
        'packages': packages,
        'branches': branches,
        'selected_branch_id': selected_branch_id,
    })



def package_add(request):
    tests = DiagnosticTest.objects.all()
    branches = Branch.objects.all()
    if request.method == 'POST':
        name = request.POST['name']
        description = request.POST['description']
        category = request.POST['category']
        price = request.POST['price']
        selected_tests = request.POST.getlist('tests')

        package = TestPackage.objects.create(
            name=name,
            description=description,
            price=price,
            category=category,
            branch_id=request.POST.get("branch")
        )
        package.tests.set(selected_tests)
        return redirect('package_list')
    return render(request, 'package_add.html', {'title': 'Add Package', 'tests': tests,"branches":branches})


def package_edit(request, id):
    package = get_object_or_404(TestPackage, id=id)
    tests = DiagnosticTest.objects.all()
    branches = Branch.objects.all()
    if request.method == 'POST':
        package.name = request.POST['name']
        package.description = request.POST['description']
        package.category = request.POST['category']
        package.price = request.POST['price']
        selected_tests = request.POST.getlist('tests')
        package.branch_id=request.POST.get("branch")
        package.save()
        package.tests.set(selected_tests)
        return redirect('package_list')

    return render(request, 'package_edit.html', {'title': 'Edit Package', 'package': package, 'tests': tests,"branches":branches,"selected_branch_id":package.branch_id})


def package_delete(request, id):
    package = get_object_or_404(TestPackage, id=id)
    package.delete()
    return redirect('package_list')


def branch(request):
    branches=Branch.objects.all()
    return render(request,"branch.html",{"branches":branches})


def branch_add(request):
    if request.method == 'POST':
        Branch.objects.create(
            name=request.POST['name'],
            address=request.POST['address'],
            pincode=request.POST['pincode'],
            contact_number=request.POST['contact_number'],
            email=request.POST.get('email', ''),
            active=True if request.POST.get('active') == 'on' else False
        )
        return redirect('branch_list')
    return render(request, 'branch_form.html', {'title': 'Add Branch'})

def branch_edit(request, id):
    branch = get_object_or_404(Branch, id=id)
    if request.method == 'POST':
        branch.name = request.POST['name']
        branch.address = request.POST['address']
        branch.pincode = request.POST['pincode']
        branch.contact_number = request.POST['contact_number']
        branch.email = request.POST.get('email', '')
        branch.active = True if request.POST.get('active') == 'on' else False
        branch.save()
        return redirect('branch_list')
    return render(request, 'branch_form.html', {'title': 'Edit Branch', 'branch': branch})

def branch_delete(request, id):
    branch = get_object_or_404(Branch, id=id)
    if request.method == 'POST':
        branch.delete()
        return redirect('branch_list')
    return render(request, 'branch_confirm_delete.html', {'branch': branch})



def user_tests(request):
    branch_id = request.GET.get('branch')
    if branch_id:
        tests = DiagnosticTest.objects.filter(branch_id=branch_id)
        most_selected_tests = DiagnosticTest.objects.order_by('-id')[:5]
    else:
        tests = DiagnosticTest.objects.all()
        most_selected_tests = DiagnosticTest.objects.order_by('-id')[:5]
    branches = Branch.objects.all()
    return render(request,"user_tests.html",{"tests":tests,"branches":branches,"most_selected_tests":most_selected_tests})



def test_detail(request, test_id):
    test = get_object_or_404(DiagnosticTest, id=test_id)
    test.views += 1
    test.save()
    branches = Branch.objects.all()
    return render(request, 'test_detail.html', {'test': test,"branches":branches})

def add_to_cart(request, test_id):
    cart = request.session.get('cart', [])
    if test_id not in cart:
        cart.append(test_id)
        request.session['cart'] = cart
    return redirect('cart')  # redirecting to cart page


def cart(request):
    branches = Branch.objects.all()
    test_ids = request.session.get('cart', [])  # existing test cart
    checkup_ids = request.session.get('checkup_cart', [])  # new checkup cart

    tests = DiagnosticTest.objects.filter(id__in=test_ids)
    checkups = Checkup.objects.filter(id__in=checkup_ids)

    total = sum(test.price for test in tests) + sum(c.price for c in checkups)

    return render(request, 'cart.html', {
        'test_items': tests,
        'checkup_items': checkups,
        'total': total,
        "branches": branches
    })



@login_required
def checkout(request):
    test_ids = request.session.get('cart', [])
    checkup_ids = request.session.get('checkup_cart', [])
    tests = DiagnosticTest.objects.filter(id__in=test_ids)
    checkups = Checkup.objects.filter(id__in=checkup_ids)
    total = sum(t.price for t in tests) + sum(c.price for c in checkups)
    branches = Branch.objects.all()

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        age = request.POST.get('age')
        gender = request.POST.get('gender')
        address = request.POST.get('address')

        # Step 1: Create Razorpay order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = client.order.create({
            "amount": int(total * 100),
            "currency": "INR",
            "payment_capture": '1'
        })

        # Step 2: Temporarily store details in session
        request.session['checkout_data'] = {
            'full_name': full_name,
            'age': age,
            'gender': gender,
            'address': address,
            'total': float(total),
            'test_ids': test_ids,
            'checkup_ids': checkup_ids
        }

        return render(request, 'payment.html', {
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key': settings.RAZORPAY_KEY_ID,
            'amount': int(total * 100),
            'org_amount':total,
            'order_info': {
                'name': full_name,
                'email': request.user.email,
                "branches": branches

            }
        })

    return render(request, 'checkout.html', {
        'test_items': tests,
        'checkup_items': checkups,
        'total': total
    })






def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm = request.POST['confirm']

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken")
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return redirect('checkout')
    branches = Branch.objects.all()

    return render(request, 'register.html',{"branches":branches})


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print(user)

        if user:
            login(request, user)
            return redirect(request.GET.get('next') or 'checkout')
        else:
            messages.error(request, "Invalid credentials")
            return redirect('login')
    branches = Branch.objects.all()

    return render(request, 'login.html',{"branches":branches})


def user_logout(request):
    logout(request)
    return redirect('login')


def checkup_list(request):
    checkups = Checkup.objects.all()
    branches = Branch.objects.all()
    return render(request, 'checkup_list.html', {'checkups': checkups,"branches":branches})
from django.utils.text import slugify
def checkup_add(request):
    tests = DiagnosticTest.objects.all()
    branches = Branch.objects.all()

    if request.method == 'POST':
        checkup = Checkup.objects.create(
            title=request.POST['title'],
            slug=slugify(request.POST['title']),
            description=request.POST['description'],
            report_time=request.POST['report_time'],
            price=request.POST['price'],
            sample_type=request.POST['sample_type'],
            target_audience=request.POST.get('target_audience', ''),
            purpose=request.POST.get('purpose', ''),
            fasting_required=True if request.POST.get('fasting_required') == 'on' else False,
            active=True if request.POST.get('active') == 'on' else False,
            branch=Branch.objects.get(id=request.POST['branch']) if request.POST.get('branch') else None
        )
        checkup.tests.set(request.POST.getlist('tests'))
        return redirect('checkup_list')

    return render(request, 'checkup_form.html', {'title': 'Add Checkup', 'tests': tests, 'branches': branches})

def checkup_edit(request, pk):
    checkup = get_object_or_404(Checkup, pk=pk)
    tests = DiagnosticTest.objects.all()
    branches = Branch.objects.all()

    if request.method == 'POST':
        checkup.title = request.POST['title']
        checkup.slug = slugify(request.POST['title'])
        checkup.description = request.POST['description']
        checkup.report_time = request.POST['report_time']
        checkup.price = request.POST['price']
        checkup.sample_type = request.POST['sample_type']
        checkup.target_audience = request.POST.get('target_audience', '')
        checkup.purpose = request.POST.get('purpose', '')
        checkup.fasting_required = True if request.POST.get('fasting_required') == 'on' else False
        checkup.active = True if request.POST.get('active') == 'on' else False
        checkup.branch = Branch.objects.get(id=request.POST['branch']) if request.POST.get('branch') else None
        checkup.save()
        checkup.tests.set(request.POST.getlist('tests'))
        return redirect('checkup_list')

    return render(request, 'checkup_form.html', {
        'title': 'Edit Checkup',
        'checkup': checkup,
        'tests': tests,
        'branches': branches
    })

def checkup_delete(request, pk):
    checkup = get_object_or_404(Checkup, pk=pk)
    if request.method == 'POST':
        checkup.delete()
        return redirect('checkup_list')
    return render(request, 'checkup_confirm_delete.html', {'checkup': checkup})


def user_checkups(request):
    branch_id = request.GET.get('branch')
    if branch_id:
        checkups = Checkup.objects.filter(active=True,branch_id=branch_id)
    else:
        checkups = Checkup.objects.filter(active=True)
    branches = Branch.objects.all()
    return render(request, 'user_checkups.html', {'checkups': checkups,"branches":branches})


def checkup_detail(request, slug):
    checkup = get_object_or_404(Checkup, slug=slug)
    checkup.views += 1
    checkup.save()
    return render(request, 'checkup_detail.html', {'checkup': checkup})

def add_checkup_to_cart(request):
    if request.method == 'POST':
        checkup_id = str(request.POST.get('checkup_id'))

        # use separate key for checkup cart items if needed
        cart = request.session.get('checkup_cart', [])
        if checkup_id not in cart:
            cart.append(checkup_id)
            request.session['checkup_cart'] = cart
            messages.success(request, "Checkup added to cart.")
        else:
            messages.info(request, "Checkup is already in your cart.")

        return redirect('cart')  # or redirect back to detail page


@login_required
def payment_success(request):
    payment_id = request.GET.get('payment_id')
    data = request.session.get('checkout_data')

    tests = DiagnosticTest.objects.filter(id__in=data['test_ids'])
    checkups = Checkup.objects.filter(id__in=data['checkup_ids'])


    order = Order.objects.create(
        user=request.user,
        full_name=data['full_name'],
        age=data['age'],
        gender=data['gender'],
        address=data['address'],
        total_amount=data['total'],
        is_paid=True
    )

    for test in tests:
        OrderItem.objects.create(order=order, item_type='test', item_name=test.name, price=test.price)

    for checkup in checkups:
        OrderItem.objects.create(order=order, item_type='checkup', item_name=checkup.title, price=checkup.price)

    # Clear session
    request.session['cart'] = []
    request.session['checkup_cart'] = []
    request.session['checkout_data'] = {}

    return redirect('thank_you')



@login_required
def thank_you(request):
    branches = Branch.objects.all()
    return render(request, 'thank_you.html',{"branches":branches})


def new_lab_orders(request):
    active_statuses = ['new', 'sample_collected', 'processing']
    filter_status = request.GET.get('status')

    if filter_status:
        orders = Order.objects.filter(status=filter_status)
    else:
        orders = Order.objects.filter(status__in=active_statuses)

    return render(request, 'new_orders.html', {
        'orders': orders,
        'status_choices': ORDER_STATUS_CHOICES,
        'current_status': filter_status or 'active'
    })

def cancelled_orders(request):
    orders = Order.objects.filter(status='cancelled')
    return render(request, 'cancelled_orders.html', {'orders': orders})

def completed_orders(request):
    orders = Order.objects.filter(status='completed')
    return render(request, 'completed_orders.html', {'orders': orders})

def upload_result(request, order_id):
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        if 'result_file' in request.FILES:
            order.result_file = request.FILES['result_file']
            order.save()
            messages.success(request, 'Result uploaded successfully.')
        else:
            messages.error(request, 'No file selected.')
    return redirect('completed_orders')

def update_order_status(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')

    if new_status in dict(ORDER_STATUS_CHOICES).keys():
        order.status = new_status
        order.save()

        # Send mail
        send_mail(
            subject=f"Order #{order.id} status updated",
            message=f"Hi {order.full_name},\nYour order status is now: {order.get_status_display()}.\n\nThank you,\nGoMart Lab",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=True
        )

        # Redirect based on status
        if new_status == 'cancelled':
            return redirect('cancelled_orders')
        elif new_status == 'completed':
            return redirect('completed_orders')

    # For all others, stay on current filtered status page
    current_status = request.GET.get('status', 'new')
    return redirect(f"{reverse('new_lab_orders')}?status={current_status}")


def print_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'invoice.html', {'order': order})


def customers(request):
    users = User.objects.filter(is_staff=False).order_by('-date_joined')
    return render(request, 'customers.html', {'users': users})


def Logout(request):
    logout(request)
    return redirect("/")

@login_required
def My_orders(request):
    status = request.GET.get('status')
    orders = Order.objects.filter(user=request.user)

    if status in ['completed', 'cancelled', 'pending', 'sample_collected', 'in_progress']:
        orders = orders.filter(status=status)

    orders = orders.order_by('-created_at')
    for order in orders:
        print(order.id, order.items.all())

    return render(request, 'my_orders.html', {
        'orders': orders,
        'selected_status': status,
    })


def view_result(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='completed')
    return render(request, 'view_result.html', {'order': order})


def download_result(request, order_id):
    order = get_object_or_404(Order, id=order_id, status='completed')

    # Let's assume result PDF file is saved as order.result_file (FileField)
    if order.result_file:
        response = FileResponse(order.result_file.open('rb'), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Result_Order_{order.id}.pdf"'
        return response
    else:
        return HttpResponse("Result not available.", status=404)




def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            return redirect('reset_password', uidb64=uid)
        except User.DoesNotExist:
            messages.error(request, "Email not found.")
    return render(request, 'forgot_password.html')


def reset_password(request, uidb64):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if request.method == 'POST':
        password = request.POST.get('password')
        confirm = request.POST.get('confirm')
        if password != confirm:
            messages.error(request, "Passwords do not match.")
        elif len(password) < 6:
            messages.error(request, "Password must be at least 6 characters.")
        else:
            user.password = make_password(password)
            user.save()
            messages.success(request, "Password updated successfully.")
            return redirect('login')
    return render(request, 'reset_password.html', {'user': user})

def remove_from_cart(request):
    if request.method == 'POST':
        item_type = request.POST.get('item_type')
        if item_type == 'test':
            cart = request.session.get('cart', [])
            item_id = int(request.POST.get('item_id'))
            if item_id in cart:
                cart.remove(item_id)
                request.session['cart'] = cart
                messages.success(request, "Test removed from cart.")
        elif item_type == 'checkup':
            checkup_cart = request.session.get('checkup_cart', [])
            item_id = request.POST.get('item_id')
            if item_id in checkup_cart:
                checkup_cart.remove(item_id)
                print(checkup_cart,"ll")
                request.session['checkup_cart'] = checkup_cart
                messages.success(request, "Checkup removed from cart.")

    return redirect('cart')

def contact(request):
    return render(request,"contact.html")

def faq(request):
    return render(request,"faq.html")

def about(request):
    return render(request, 'about.html')


def blog_list(request):
    blogs = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'blog_list.html', {'blogs': blogs})

def blog_detail(request, slug):
    blog = BlogPost.objects.get(slug=slug)
    return render(request, 'blog_detail.html', {'blog': blog})


def admin_blog_list(request):
    blogs = BlogPost.objects.all().order_by('-created_at')
    return render(request, 'admin_blog_list.html', {'blogs': blogs})

def admin_blog_add(request):
    if request.method == 'POST':
        title = request.POST['title']
        slug = slugify(title)
        content = request.POST['content']
        image = request.FILES.get('image')

        BlogPost.objects.create(
            title=title, slug=slug, content=content, image=image
        )
        return redirect('admin_blog_list')
    return render(request, 'admin_blog_form.html')

def admin_blog_edit(request, id):
    blog = get_object_or_404(BlogPost, id=id)
    if request.method == 'POST':
        blog.title = request.POST['title']
        blog.slug = slugify(blog.title)
        blog.content = request.POST['content']
        if 'image' in request.FILES:
            blog.image = request.FILES['image']
        blog.save()
        return redirect('admin_blog_list')
    return render(request, 'admin_blog_form.html', {'blog': blog})

def admin_blog_delete(request, id):
    blog = get_object_or_404(BlogPost, id=id)
    blog.delete()
    return redirect('admin_blog_list')


def My_Account(request):
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.save()
        messages.success(request, "Your profile has been updated.")
        return redirect('My_Account')

    return render(request, "My_Account.html")

def change_password(request):
    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')

        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
        else:
            request.user.set_password(new_password1)
            request.user.save()
            update_session_auth_hash(request, request.user)  # Keep user logged in
            messages.success(request, 'Password updated successfully.')
    return redirect('My_Account')