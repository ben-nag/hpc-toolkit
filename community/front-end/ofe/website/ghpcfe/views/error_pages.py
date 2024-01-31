# Copyright 2022 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Custom error page renderers"""

from django.shortcuts import render

def custom_error_403(request, unused_exception):
    return render(request, '403.html', {})

def custom_error_500(request, exception=False):
    exception_error = request.META["ExceptionErr"]
    return render(request, 'error500.html', {'erroutput':exception_error})

def custom_error_404 (request, exception):
    error_to_show = "Error 404: File not found"
    return render (request, 'error404.html',{"erroutput":error_to_show})