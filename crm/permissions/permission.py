from django.shortcuts import HttpResponse,render,redirect
from django.urls import resolve
from crm.permissions import permission_list

def perm_check(*args,**kwargs):
    request = args[0]
    if request.user.is_authenticated:
    # 打印一个user对象，利用user对象的is_tuthenticated方法做判断，是否验证过，返回布尔值，，做判断
    # 用户登录后才能访问某些页面，
    # 没有登录就访问，就直接跳到登录页面，
    # 用户跳转到登录页面完成登录，自动访问跳转到之前访问的地址，
        for permission_name, v in permission_list.perm_dic.items():
            url_matched = False
            print("路径", request.path)
            if v['url_type'] == 1:
                if v['url'] == request.path:    #绝对url匹配上
                    url_matched = True
            else:
                #把绝对的url请求转成相对的url_name
                resolve_url_obj = resolve(request.path)  #作用： 从url得到相互映射的url_name
                if resolve_url_obj.url_name == v['url']:
                    url_matched =True

            if url_matched:
                print("url matched...")
                if v['method'] == request.method:  #请求方法也匹配上
                    arg_matched = True
                    for request_arg in v['args']:
                        request_method_func = getattr(request,v['method'])
                        if not request_method_func.get(request_arg):
                            arg_matched = False

                    if arg_matched: #走到这里，仅代表这个请求 和这条权限的定义规则 匹配上了
                        print("arg matched...")
                        if request.user.has_perm(permission_name):
                            #有权限
                            print("有权限",permission_name)
                            return True
    else:
        return redirect("http://127.0.0.1:8000/account/login/")

def check_permission(func):
    print("--------check_permission")
    def inner(*args,**kwargs):
        print("--permission:",*args,**kwargs)
        print("--func",func)
        if perm_check(*args,**kwargs) is True:
            return func(*args,**kwargs)
        else:
            return HttpResponse("沒权限")
    return inner