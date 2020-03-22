from django.db import models
from crm import models
from django.shortcuts import render,redirect,HttpResponse

enabled_admins = {}

class BaseAdmin(object):
    list_display = []
    list_filters = []
    search_fields = []
    list_per_page = 5
    ordering = None
    actions = ["delete_selected_objs",]
    readonly_fields = []
    readonly_table = False
    modelform_exclude_fields = []

    def delete_selected_objs(self,request,querysets):
        app_name = self.model._meta.app_label
        table_name = self.model._meta.model_name
        print("delete_selected_objs",self,request,querysets)
        if self.readonly_table:
            errors = {'readonly_table': 'This table is readonly,cannot be deleted or modifield'}
        else:
            errors = {}
        if request.POST.get("delete_confirm") == "yes":
            if not self.readonly_table:
                querysets.delete()
                return redirect("/king_admin/%s/%s/" %(app_name,table_name))
        selected_ids = ','.join([str(i.id) for i in querysets])
        return render(request,"king_admin/table_obj_delete.html",{"objs":querysets,
                                                              "admin_class":self,
                                                              "app_name": app_name,
                                                              "table_name": table_name,
                                                              "selected_ids":selected_ids,
                                                              "action":request._admin_action,
                                                              "errors":errors})

    def default_form_validation(self):
        '''用户可以在此进行自定义的表单验证，相当于django form的clean方法'''
        pass



class CustomerAdmin(BaseAdmin):
    list_display = ['id','qq','name','source','consultant','consult_course','status','date','enroll']
    list_filters = ['source','consultant','consult_course','status','date']
    search_fields = ['qq', 'name','consultant__name']  # 搜索字段
    list_per_page = 5
    ordering = "id"
    filter_horizontal = ('tags',)  # ManyToMany多对多字段,编辑页面设置
    readonly_fields = ['qq','consultant','tags']
    readonly_table = False

    actions = ["delete_selected_objs", "test"]
    def test(self,request,querysets):
        print("test")
    test.display_name = "测试动作"

    def enroll(self):
        if self.instance.status == 1:
            link_name = "报名新课程"
        else:
            link_name = "报名"
        return '''<a href='http://127.0.0.1:8000/crm/customer/%s/enrollment/'>%s</a>''' % (self.instance.id,link_name)
    enroll.display_name = "报名链接"

    def default_form_validation(self):
        consult_content = self.cleaned_data.get("content", '')
        if len(consult_content) < 15:
            return self.ValidationError(('Field %(field)s 咨询内容记录不能少于15个字符 '),
                                      code="invalid",
                                      params={'field': "content",},)

    def clean_name(self):
        if not self.cleaned_data["name"]:
            self.add_error('name', "cannot be null")
        else:
            return self.cleaned_data["name"]


class UserProfileAdmin(BaseAdmin):
    list_display = ['email','name']
    readonly_fields = ["password",]
    filter_horizontal = ('user_permissions',"groups")
    modelform_exclude_fields = ['last_login',]

class CustomerFollowUpAdmin(BaseAdmin):
    list_display = ['customer','consultant','date']




class CourseRecordAdmin(BaseAdmin):
    list_display = ['from_class','day_num','teacher','has_homework','homework_title','date']

    def initialize_studyrecords(self,request,queryset):
        if len(queryset) > 1:
            return HttpResponse("只能选择一个班级")
        print(queryset[0].from_class.enrollment_set.all())
        for enroll_obj in queryset[0].from_class.enrollment_set.all():
            # models.StudyRecord.objects.get_or_create(
            #     student=enroll_obj,
            #     course_record=queryset[0],
            #     attendance=0,
            #     score=0,
            # )
            new_obj_list = []
            new_obj_list.append(models.StudyRecord(
                student=enroll_obj,
                course_record=queryset[0],
                attendance=0,
                score=0,
            ))
            try:
                models.StudyRecord.objects.bulk_create(new_obj_list)  #.bulk_create()批量创建对象，减少SQL查询次数
            except Exception as e:
                return HttpResponse("批量初始化学习记录失败，请检查该节课是否已经有对应学习记录")
        return redirect("http://127.0.0.1:8000/king_admin/crm/studyrecord/?course_record=%s" % queryset[0].id)
    actions = ['initialize_studyrecords', ]
    initialize_studyrecords.display_name = "初始化本节所有学员的上课记录"

class StudyRecordAdmin(BaseAdmin):
    list_display = ['student','course_record','attendance','score','date']
    list_filters = ["course_record",'attendance','score']
    list_editable = ['attendance','score']
    # search_fields = ['course_record','attendance','score']

def register(models_class,admin_class=None):
    '''
    models_class._meta.app_label:通过models类名获取，app名
    models_class._meta.model_name:通过models类名，获取表名
    models_class.CourseRecord._meta.verbose_name:通过models类名，获取表别名
    '''
    if models_class._meta.app_label not in enabled_admins:
        enabled_admins[models_class._meta.app_label] = {}

    admin_class.model = models_class
    enabled_admins[models_class._meta.app_label][models_class._meta.model_name] = admin_class

register(models.Customer,CustomerAdmin)
register(models.CustomerFollowUp,CustomerFollowUpAdmin)
# register(models.Enrollment)
# register(models.Course)
# register(models.ClassList)
register(models.CourseRecord,CourseRecordAdmin)
# register(models.Branch)
# register(models.Role)
# register(models.Payment)
register(models.StudyRecord,StudyRecordAdmin)
# register(models.Tag)
register(models.UserProfile,UserProfileAdmin)
# register(models.Menu)