from django.shortcuts import render,HttpResponse,redirect
from crm import forms,models
from django.db import IntegrityError
import string,random
from django.core.cache import cache
import os
from PerfectCRM.settings import ENROLLED_DATA

# Create your views here.
def index(request):

    return render(request,"index.html")

def customer_list(request):
    return render(request,"sales/customers.html")


def enrollment(request,customer_id):
    customer_obj = models.Customer.objects.get(id=customer_id)
    msgs = {}
    if request.method == "POST":
        enroll_form = forms.EnrollmentForm(request.POST)
        if enroll_form.is_valid():
            msg = '''请将此链接发送给客户进行填写http://127.0.0.1:8000/crm/customer/registration/{enroll_obj_id}/{random_str}'''
            random_str = "".join(random.sample(string.ascii_lowercase + string.digits, 8))
            try:
                enroll_form.cleaned_data["customer"] = customer_obj
                enroll_obj = models.Enrollment.objects.create(**enroll_form.cleaned_data)
                msgs["msg"] = msg.format(enroll_obj_id=enroll_obj.id,random_str=random_str)
            except IntegrityError as e:
                enroll_obj = models.Enrollment.objects.get(customer_id=customer_obj.id,
                                                           enrolled_class_id=enroll_form.cleaned_data["enrolled_class"].id)
                if enroll_obj.contract_agreed:  #确认学生是否已经同意
                    return redirect("/crm/contract_review/%s" % enroll_obj.id)
                enroll_form.add_error("__all__","该用户的此条报名信息已存在，不能重复创建")
                msgs["msg"] = msg.format(enroll_obj_id=enroll_obj.id,random_str=random_str)
            cache.set(enroll_obj.id, random_str, 3000)
    else:
        enroll_form = forms.EnrollmentForm()
    return render(request,"sales/enrollment.html",{"enroll_form": enroll_form,
                                                   "customer_obj": customer_obj,
                                                   "msgs": msgs})

def stu_registration(request,enroll_id,random_str):
    if cache.get(enroll_id) == random_str:
        enroll_obj = models.Enrollment.objects.get(id=enroll_id)
        if request.method == "POST":

            #处理前端上传过来的文件
            if request.is_ajax():    #上传图片，前端使用的是ajax方式上传
                print("ajax----",request.FILES)
                enroll_data_dir = "%s/%s" %(ENROLLED_DATA,enroll_id)
                if not os.path.exists(enroll_data_dir):    #如果path存在,返回True;如果path不存在,返回False
                    os.makedirs(enroll_data_dir,exist_ok=True)
                for k, file_obj in request.FILES.items():   #获取上传的图片，然后保存
                    with open("%s/%s" % (enroll_data_dir,file_obj.name),"wb+") as destination:
                        for chunk in file_obj.chunks():
                            destination.write(chunk)
                return HttpResponse("上传成功")

            customer_form = forms.CustomerForm(request.POST,instance=enroll_obj.customer)
            if customer_form.is_valid():
                customer_form.save()
                enroll_obj.contract_agreed = True
                enroll_obj.save()
                return render(request,"sales/stu_registration.html",{"status":1})
        else:
            if enroll_obj.contract_agreed == True:
                status = 1
            else:
                status = 0
            customer_form = forms.CustomerForm(instance=enroll_obj.customer)
        return render(request,"sales/stu_registration.html",{"customer_form":customer_form,
                                                         "enroll_obj":enroll_obj,"status":status})
    else:
        return HttpResponse("去你妈的臭傻逼，想黑我")

def contract_review(request,enroll_id):
    '''合同评审'''
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    enroll_form = forms.EnrollmentForm(instance=enroll_obj)
    customer_form = forms.CustomerForm(instance=enroll_obj.customer)
    return render(request, "sales/contract_review.html", {"enroll_obj":enroll_obj,
                                                 "customer_form":customer_form,
                                                 "enroll_form":enroll_form})


def payment(request,enroll_id):
    '''缴费记录'''
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    errors = []
    if request.method == "POST":
        payment_amount = request.POST.get("amount")
        if payment_amount:
            payment_amount = int(payment_amount)
            if payment_amount < 500:
                errors.append("缴费金额不得低于500元")
            else:
                payment_obj = models.Payment.objects.create(
                    customer= enroll_obj.customer,
                    course= enroll_obj.enrolled_class.course,
                    amount= payment_amount,
                    consultant = enroll_obj.consultant
                )
                enroll_obj.contract_agreed = True
                enroll_obj.save()

                enroll_obj.customer.status = 1
                enroll_obj.customer.save()
                return redirect("http://127.0.0.1:8000/king_admin/crm/customer/")

        else:
            errors.append("必须要输入缴费金额")
    return render(request, "sales/payment.html", {"enroll_obj":enroll_obj,
                                                  "erorrs":errors})

def enrollment_rejection(request,enroll_id):
    '''驳回合同'''
    enroll_obj = models.Enrollment.objects.get(id=enroll_id)
    enroll_obj.contract_agreed = False
    enroll_obj.save()
    return redirect("http://127.0.0.1:8000/crm/customer/%s/enrollment" % enroll_obj.customer.id)


