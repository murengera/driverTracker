from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Location)
admin.site.register(Trip)
admin.site.register(Route)
admin.site.register(Stop)
admin.site.register(Log)