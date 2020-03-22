
from django.urls import path,re_path
from crm import views

urlpatterns = [
    path('',views.index,name="sales_index"),
    # path('stu_index/',views.stu_index,name="stu_index"),
    path('customers/',views.customer_list,name="customer_list"),
    re_path('^customer/(\d+)/enrollment/$', views.enrollment, name="enrollment"),
    re_path('^customer/registration/(\d+)/(\w+)/$', views.stu_registration, name="stu_registration"),
    re_path('^contract_review/(\d+)/$', views.contract_review, name="contract_review"),
    re_path('^enrollment_rejection/(\d+)/$', views.enrollment_rejection, name="enrollment_rejection"),
    re_path('^payment/(\d+)/$', views.payment, name="payment"),
]

