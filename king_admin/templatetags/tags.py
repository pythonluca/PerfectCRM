
from django.utils.timezone import datetime,timedelta
from django import template
from django.utils.safestring import mark_safe
from django.core.exceptions import FieldDoesNotExist

register = template.Library()

@register.simple_tag()
def render_app_name(admin_class):
    return admin_class.model._meta.verbose_name


@register.simple_tag()
def get_query_sets(admin_class):
    return admin_class.model.objects.all()

@register.simple_tag()
def build_table_row(request,obj,admin_class):
    row_ele = ""
    for index, column in enumerate(admin_class.list_display):
        try:
            field_obj = obj._meta.get_field(column)
            if field_obj.choices:
                column_data = getattr(obj, "get_%s_display" % (column))()  # 显示choice里面的显示字段get_字段名_display
            else:
                column_data = getattr(obj, column)  # 不能直接用obj.column,因为column是一个字符串，不是一个属性
            if type(column_data).__name__ == "datetime":
                column_data = column_data.strftime("%Y-%m-%d %H:%M:%S")
            if index == 0:  # add a tag，可以跳转到修改页
                print(request.path)
                column_data = "<a href='{request_path}{obj_id}/change/'>{data}</a>".format(request_path=request.path,
                                                                                           obj_id=obj.id,
                                                                                           data=column_data)
        except FieldDoesNotExist as e:
            if hasattr(admin_class,column):
                column_func = getattr(admin_class,column)
                admin_class.instance = obj
                admin_class.request = request
                column_data = column_func()
        row_ele += "<td>%s</td>" %(column_data)
    return mark_safe(row_ele)

@register.simple_tag()
def render_filter_ele(filter_field,admin_class,filter_conditions):
    select_ele = '''<select class="form-control" name={filter_field} ><option value="">----</option>'''
    field_obj = admin_class.model._meta.get_field(filter_field)
    if field_obj.choices:
        selected = ""
        for choice_item in field_obj.choices:
            if filter_conditions.get(filter_field) == str(choice_item[0]):
                selected = "selected"
            select_ele += '''<option value='%s' %s>%s</option>''' %(choice_item[0],selected,choice_item[1])
            selected = ""

    if type(field_obj).__name__ == "ForeignKey":
        selected = ""
        for choice_item in field_obj.get_choices()[1:]:
            if filter_conditions.get(filter_field) == str(choice_item[0]):
                selected = "selected"
            select_ele += '''<option value='%s' %s>%s</option>''' % (choice_item[0], selected, choice_item[1])
            selected = ""
    if type(field_obj).__name__ in ["DateTimeField", "DateField"]:
        date_els = []
        today_ele = datetime.now().date()
        date_els.append(['今天',datetime.now().date()])
        date_els.append(['昨天', today_ele- timedelta(days=1)])
        date_els.append(['近7天', today_ele- timedelta(days=7)])
        date_els.append(['本月', today_ele.replace(day=1)])
        date_els.append(['近30天', today_ele - timedelta(days=30)])
        date_els.append(['近90天', today_ele - timedelta(days=90)])
        date_els.append(['近180天', today_ele - timedelta(days=180)])
        date_els.append(['本年', today_ele.replace(month=1,day=1)])
        date_els.append(['近一年', today_ele - timedelta(days=365)])
        selected = ''
        for item in date_els:
            select_ele += '''<option value='%s' %s>%s</option>''' % (item[1], selected, item[0])
        filter_field_name = "%s__gte" % filter_field
    else:
        filter_field_name = filter_field
    select_ele += "</select>"
    select_ele = select_ele.format(filter_field=filter_field_name)
    return mark_safe(select_ele)

# @register.simple_tag()
# def render_page_ele(loop_counter,query_sets,filter_conditions):
#     '''query_sets.number 该页的页码'''
#     filters = ""
#     for k,v in filter_conditions.items():
#         filters += "&%s=%s" % (k, v)
#     if loop_counter < 3 or loop_counter > query_sets.paginator.num_pages - 2:  #代表这是前2页 or 这是后2页
#         ele_class = ""
#         if query_sets.number == loop_counter:
#             ele_class = "active"
#         ele = '''<li class="%s"><a href="?page=%s%s">%s</a></li>''' % (ele_class, loop_counter, filters, loop_counter)
#         return mark_safe(ele)
#
#     if abs(query_sets.number - loop_counter) <= 1:
#         ele_class = ""
#         if query_sets.number == loop_counter:
#             ele_class = "active"
#         ele = '''<li class="%s"><a href="?page=%s%s">%s</a></li>''' %(ele_class,loop_counter,filters,loop_counter)
#         return mark_safe(ele)
#     else:
#         return "---"
#
#     return ""

@register.simple_tag()
def build_paginators(query_sets, filter_conditions, previous_orderby, search_text):
    '''返回整个分页元素'''
    page_btns = ""
    filters = ""
    for k, v in filter_conditions.items():
        filters += "&%s=%s" % (k, v)
    added_dot_ele = False
    for page_num in query_sets.paginator.page_range:
        if page_num <3 or page_num > query_sets.paginator.num_pages - 2 \
            or abs(query_sets.number - page_num) <= 1:  #代表这是前2页 or 这是后2页 or判断前后1页
            ele_class = ""
            if query_sets.number == page_num:
                added_dot_ele = False
                ele_class = "active"
            page_btns += '''<li class="%s"><a href="?page=%s%s&o=%s&_q=%s">%s</a></li>''' % (
            ele_class, page_num, filters, previous_orderby, search_text, page_num)
        else:   #显示···
            if added_dot_ele == False:   #现在还没加...
                page_btns += "<li><a>...</a></li>"
                added_dot_ele = True
    return mark_safe(page_btns)

@register.simple_tag()
def selection_filter_conditions(filter_conditions,previous_orderby):
    '''给上下页按钮，增加过滤条件'''
    filters = ""
    for k, v in filter_conditions.items():
        filters += "&%s=%s&o=%s" % (k, v, previous_orderby)
    return filters

@register.simple_tag()
def build_table_header_column(column, orderby_key, filter_conditions,admin_class):
    filters = ""
    ele = '''<th><a href="?{filters}o={orderby_key}">{column}</a>{sort_icon}</th>'''
    for k, v in filter_conditions.items():
        filters += "%s=%s&" % (k, v)
    if orderby_key:
        if orderby_key.startswith("-"):
            sort_icon = '''<span class="glyphicon glyphicon-chevron-up" aria-hidden="true"></span>'''
        else:
            sort_icon = '''<span class="glyphicon glyphicon-chevron-down" aria-hidden="true"></span>'''
        if orderby_key.strip("-") == column:  #排序的就是这个字段
            orderby_key = orderby_key
        else:
            orderby_key = column
            sort_icon = ''
    else:
        orderby_key = column
        sort_icon = ''
    try:
        column_verbose_name = admin_class.model._meta.get_field(column).verbose_name.upper()
    except FieldDoesNotExist as e:
        column_verbose_name = getattr(admin_class,column).display_name.upper()
        ele = '''<th><a href="javascript:void(0);">{column}</a></th>'''.format(column=column_verbose_name)
        return mark_safe(ele)
    ele = ele.format(filters=filters, orderby_key=orderby_key, column=column_verbose_name, sort_icon=sort_icon)
    return mark_safe(ele)

@register.simple_tag()
def get_model_name( admin_class):
    return admin_class.model._meta.verbose_name

@register.simple_tag()
def get_m2m_obj_list(admin_class,field,form_obj):
    '''返回tags的所有待选数据'''
    #表结构对象的某个字段
    field_obj = getattr(admin_class.model,field.name)
    all_obj_list = field_obj.rel.model.objects.all()

    #单条数据的对象中的某个字段
    if form_obj.instance.id:
        obj_instance_field = getattr(form_obj.instance, field.name)
        selected_obj_list = obj_instance_field.all()
    else: #代表这是在添加页面
        return all_obj_list
    standy_obj_liat = []
    for obj in all_obj_list:
        if obj not in selected_obj_list:
            standy_obj_liat.append(obj)
    return standy_obj_liat

@register.simple_tag()
def get_m2m_selected_obj_list(form_obj,field):
    '''返回tags的已选择数据'''
    if form_obj.instance.id:
        field_obj = getattr(form_obj.instance,field.name)
        return field_obj.all()

@register.simple_tag()
def display_obj_related(objs):
    '''把对象所有相关联的数据取出来'''
    try:
        if objs:
            objs.query     #如果有query属性，说明是queryset类型
            return mark_safe(recursive_related_objs_loolup(objs))
    except:
        if objs:
            objs = [objs,]
            return mark_safe(recursive_related_objs_loolup(objs))


def recursive_related_objs_loolup(objs):
    ul_ele = "<ul>"
    for obj in objs:
        li_ele = '''<li> %s:%s </li>''' %(obj._meta.verbose_name,obj.__str__().strip("<>"))
        ul_ele += li_ele

        for m2m_field in obj._meta.local_many_to_many:   #查询出本moels对象的所有ManyToManyField
            sub_ul_ele = "<ul>"
            m2m_field_obj = getattr(obj,m2m_field.name)
            for i in m2m_field_obj.all():
                li_ele = '''<li> %s:%s </li>''' % (m2m_field.verbose_name, i.__str__().strip("<>"))
                sub_ul_ele += li_ele
            sub_ul_ele += "</ul>"
            ul_ele += sub_ul_ele

        for related_obj in obj._meta.related_objects:    #获取所有通过ForeignKey关联Customer表的信息
            if 'ManyToManyRel' in related_obj.__repr__():
                if hasattr(obj, related_obj.get_accessor_name()):
                    accessor_obj = getattr(obj, related_obj.get_accessor_name())
                    if hasattr(accessor_obj, 'all'):
                        target_objs = accessor_obj.all()
                        sub_ul_ele = "<ul style='color:red'>"
                        for o in target_objs:
                            li_ele = '''<li> %s:%s </li>''' % (o._meta.verbose_name, o.__str__().strip("<>"))
                            sub_ul_ele += li_ele
                        sub_ul_ele += "</ul>"
                        ul_ele += sub_ul_ele

            elif hasattr(obj, related_obj.get_accessor_name()):   #related_obj.get_accessor_name() 获取到这个反向查询的:表名_set
                accessor_obj = getattr(obj, related_obj.get_accessor_name())
                if hasattr(accessor_obj,'all'):   #查询外键关联的所有对象
                    target_objs = accessor_obj.all()
                    print("target_objs",target_objs)
                else:
                    print("one to one i guess:",accessor_obj)
                    target_objs = accessor_obj
                if len(target_objs) > 0:
                    nodes = recursive_related_objs_loolup(target_objs)
                    ul_ele += nodes
    ul_ele += "</ul>"
    return ul_ele

@register.simple_tag()
def get_action_verbose_name(admin_class, action):
    action_func = getattr(admin_class,action)
    return action_func.display_name if hasattr(action_func,"display_name") else action


