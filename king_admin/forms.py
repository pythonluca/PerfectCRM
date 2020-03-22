from django.forms import forms,ModelForm
from crm import models
from django.forms import ValidationError
from django.utils.translation import ugettext as _

'''类也是一个对象，类这个对象是由type生成的
    类默认是由type类实例化产生，type类中如何实现的创建类？类又是如何创建对象？
    答：类中有一个属性__metaclass__,其用来表示该类由谁来实例化创建，所以，我们可以为__metaclass__设置一个type类的派生类，从而查看类创建的过程
    class MyType(type):
        def __init__(self,what,bases=None,dict=None)
            super(MyType,self).__init__(what,bases,dict)
        def __call__(self,*args,**kwargs):
            obj = self.__new__(self,*args,**kwargs)
            self.__init(obj)
    
    class Foo(object):
        ____metaclass__ = MyType
        
    #类的特殊创建方式：
    def func(self):
        print("heel alex")
    
    Foo = type("Foo",(object,),{'func':func})
    #type第一个参数：类名
    #type第二个参数：当前类的基类
    #type第三个参数：类的成员    
'''
class CustomerModelForm(ModelForm):
    class Meta:
        model = models.Customer
        fields = "__all__"   #直接在class Meta中使用fields = “__all__”就可以加载我们表中所有的字段



def create_model_form(request,admin_class):
    '''在models_form里面添加属性'''
    def __new__(cls, *args, **kwargs):
        for field_name,field_obj in cls.base_fields.items():
            field_obj.widget.attrs['class'] = 'form-control'   #在modelform里面添加class属性值
            # field_obj.widget.attrs['maxlength'] = getattr(field_obj, "max_length") if hasattr(field_obj, "max_length") else ""

            if not hasattr(admin_class,"is_add_form"):
                if field_name in admin_class.readonly_fields:
                    field_obj.widget.attrs['disabled'] = 'disabled'

            if hasattr(admin_class,"clean_%s" % field_name):
                field_clean_func = getattr(admin_class,"clean_%s" % field_name)
                setattr(cls, "clean_%s" % field_name, field_clean_func)
        return ModelForm.__new__(cls)

    def default_clean(self):
        '''给所有的form加一个clean验证'''
        error_list = []
        print("cleaned data:", self.cleaned_data)
        if self.instance.id:  #如果有值代表是修改的表单，如果没有值，代表是添加页面
            for field in admin_class.readonly_fields:
                field_val = getattr(self.instance,field)   #从数据库取对象中字段的value值
                field_val_from_frontend = self.cleaned_data.get(field)  # 从前端返回的value值
                if hasattr(field_val, 'all'):  #代表是没m2m
                    m2m_objs = field_val.all()
                    m2m_vals = [i[0] for i in m2m_objs.values_list("id")]
                    set_m2m_vals = set(m2m_vals)
                    field_vals_from_frontend = [i[0] for i in field_val_from_frontend.values_list("id")]
                    set_m2m_vals_from_frontend = set(field_vals_from_frontend)
                    if set_m2m_vals != set_m2m_vals_from_frontend:
                        # error_list.append(ValidationError(_('Field %(field)s is Readonly'),
                        #                                   code="invalid",
                        #                                   params={'field': field}, ))
                        self.add_error(field, "readonly field")
                    continue

                if field_val != field_val_from_frontend:
                    error_list.append(ValidationError(_('Field %(field)s is Readonly,data should be %(val)s '),
                                          code="invalid",
                                          params={'field': field, "val": field_val},))

        #readonly_table check
        if admin_class.readonly_table:
            raise error_list.append(ValidationError(_('table is Readonly,cannot be modifield or added'),
                                    code="invalid",))

        # invoke user's customer form validation
        self.ValidationError = ValidationError
        response = admin_class.default_form_validation(self)
        if response:
            error_list.append(response)

        if error_list:
            raise ValidationError(error_list)


    '''动态生成model form'''
    class Meta:
        model = admin_class.model
        fields = "__all__"  # 直接在class Meta中使用fields = “__all__”就可以加载我们表中所有的字段
        exclude = admin_class.modelform_exclude_fields   #动态去掉field

    attrs = {"Meta": Meta}
    _model_corm_class = type("DynamicModelForm",(ModelForm,),attrs)   #类的特殊创建方式：
    setattr(_model_corm_class, "__new__", __new__)   #setattr用于设置属性值,如果属性不存在会创建一个新的对象属性
    setattr(_model_corm_class, "clean", default_clean)
    return _model_corm_class