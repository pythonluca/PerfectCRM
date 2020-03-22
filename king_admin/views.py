from django.shortcuts import render,redirect
from king_admin import king_admin
from king_admin.utils import table_filter,table_sort,table_search
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
import importlib
from king_admin.forms import create_model_form
import re
from django.contrib.auth.decorators import login_required
from crm.permissions import permission
# Create your views here.

@login_required
def index(request):

    return render(request, "king_admin/table_index.html", {'tables_list': king_admin.enabled_admins})

@login_required
@permission.check_permission
def display_table_objs(request,app_name,table_name):
    # model_module = importlib.import_module('%s.models' %(app_name))   #通过字符串获取models文件
    # model_obj = getattr(model_module,table_name)
    admin_class = king_admin.enabled_admins[app_name][table_name]
    if request.method == "POST":   #action来了
        selected_ids = request.POST.get("selected_ids")
        action = request.POST.get("action")
        if selected_ids:
            selected_obj = admin_class.model.objects.filter(id__in=selected_ids.split(','))
        else:
            raise KeyError("No object selected.")
        if hasattr(admin_class,action):
            action_func = getattr(admin_class, action)
            request._admin_action = action
            return action_func(admin_class, request, selected_obj)


    object_list,filter_conditions = table_filter(request,admin_class)  #过滤后的结果
    object_list = table_search(request,admin_class,object_list)

    object_list,orderby_key = table_sort(request, object_list)  #排序后的结果
    paginator = Paginator(object_list,admin_class.list_per_page)   # 先拿到分页器对象，第一个参数：对象列表，第二个参数：每页显示的条数
    page = request.GET.get("page")
    try:
        query_sets = paginator.page(page) # 取某一页，返回一个对象
    except PageNotAnInteger:      # page不是int类型
        query_sets = paginator.page(1)
    except EmptyPage:             # 如果传递的page不在我们的分页范围中
        query_sets = paginator.page(paginator.num_pages)   #paginator.num_pages  总页数
    return render(request, "king_admin/table_objs.html", {"admin_class": admin_class,
                                                          "query_sets": query_sets,
                                                          "orderby_key": orderby_key,
                                                          "filter_conditions": filter_conditions,
                                                          "previous_orderby":request.GET.get("o", ''),
                                                          "search_text":request.GET.get('_q','')})

@login_required
@permission.check_permission
def table_obj_change(request,app_name,table_name,obj_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    model_form_class = create_model_form(request,admin_class)
    obj = admin_class.model.objects.get(id=obj_id)
    if request.method == "POST":
        # form_obj = model_form_class(request.POST)  #request.POST,获取提交后数据,创建
        form_obj = model_form_class(request.POST, instance=obj)  # request.POST,获取提交后,指定修改对象，更新
        if form_obj.is_valid():
            form_obj.save()

            c1 = re.compile(r"/[0-9]+/change/")
            redirect_table = c1.sub('/', request.path)
            return redirect(redirect_table)
    else:
        form_obj = model_form_class(instance=obj)   #instance=obj,即指定这次的修改对象
    return render(request, "king_admin/table_obj_change.html", {"form_obj":form_obj,
                                                              "admin_class":admin_class,
                                                              "app_name":app_name,
                                                              "table_name":table_name})

@login_required
@permission.check_permission
def table_obj_add(request,app_name,table_name):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    admin_class.is_add_form = True
    model_form_class = create_model_form(request, admin_class)
    if request.method == "POST":
        form_obj = model_form_class(request.POST)  #request.POST,获取提交后数据,创建
        if form_obj.is_valid():
            form_obj.save()
            return redirect(request.path.replace("/add/", "/"))
    else:
        form_obj = model_form_class()   #instance=obj,即指定这次的修改对象

    return render(request, "king_admin/table_obj_add.html",{"form_obj":form_obj,
                                                           "admin_class":admin_class,
                                                            "app_name": app_name,
                                                            "table_name": table_name})

@login_required
def table_obj_delete(request,app_name,table_name,obj_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    obj = admin_class.model.objects.get(id=obj_id)
    if admin_class.readonly_table:
        errors = {'readonly_table': 'table is readonly,obj [%s] cannot be deleted' % obj}
    else:
        errors = {}
    if request.method == "POST":
        if not admin_class.readonly_table:
            obj.delete()
            return redirect("/king_admin/%s/%s" % (app_name, table_name))


    return render(request,"king_admin/table_obj_delete.html",{"objs":obj,
                                                              "admin_class":admin_class,
                                                              "app_name": app_name,
                                                              "table_name": table_name,
                                                              "errors":errors})

@login_required
def password_reset(request,app_name,table_name,obj_id):
    admin_class = king_admin.enabled_admins[app_name][table_name]
    model_form_class = create_model_form(request, admin_class)
    obj = admin_class.model.objects.get(id=obj_id)
    errors = {}
    if request.method == "POST":
        _password1 = request.POST.get("password1")
        _password2 = request.POST.get("password2")
        if _password1 == _password2:
            if len(_password2) >5:
                obj.set_password(_password1)
                obj.save()
                return redirect(request.path.rstrip("password/"))
            else:
                errors['password_too_short'] = "must not less than 6 letters"

        else:
            errors['invalid_password'] = "password are not the same"
    return render(request,"king_admin/password_reset.html",{"obj":obj,
                                                            "errors":errors})





