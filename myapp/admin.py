from django.contrib import admin
from .models import KeyValueData, SurveyResponse

# Register your models here.
admin.site.register(KeyValueData)
admin.site.register(SurveyResponse)