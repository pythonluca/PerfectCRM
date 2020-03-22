from django.forms import ModelForm
from crm import models

class EnrollmentForm(ModelForm):
    def __new__(cls, *args, **kwargs):
        for field_name,field_obj in cls.base_fields.items():
            field_obj.widget.attrs['class'] = 'form-control'   #在modelform里面添加class属性值
        return ModelForm.__new__(cls)

    class Meta:
        model = models.Enrollment
        fields = ['enrolled_class','consultant']

class CustomerForm(ModelForm):
    def __new__(cls, *args, **kwargs):
        for field_name,field_obj in cls.base_fields.items():
            field_obj.widget.attrs['class'] = 'form-control'   #在modelform里面添加class属性值
            if field_name in cls.Meta.readonly_fields:
                field_obj.widget.attrs['disabled'] = 'disabled'
        return ModelForm.__new__(cls)

    def clean_qq(self):
        print(self.instance.qq)
        print(self.cleaned_data['qq'])
        if self.instance.qq != self.cleaned_data['qq']:
            self.add_error("qq","傻逼你还尝试黑我！")
        else:
            return self.cleaned_data['qq']

    class Meta:
        model = models.Customer
        fields = "__all__"
        exclude = ['tags','content','memo','status','referral_from','consult_course']   #不让显示的的项
        readonly_fields = ['qq','consultant','source']

class PaymentForm(ModelForm):
    def __new__(cls, *args, **kwargs):
        for field_name,field_obj in cls.base_fields.items():
            field_obj.widget.attrs['class'] = 'form-control'   #在modelform里面添加class属性值
        return ModelForm.__new__(cls)

    class Meta:
        model = models.Payment
        fields = "__all__"
