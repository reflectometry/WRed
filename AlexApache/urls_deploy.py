#Author: Joe Redmon
#urls.py

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from WRed.display.views import *
from django.contrib.auth.views import login, logout
# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

from WRed.display.models import DataFile, MetaData

urlpatterns = patterns('',
    (r'^files/all$',all_files),
    (r'^files/all/$',all_files),
    (r'^files/forms/download/$', download),
    (r'^files/forms/download/batch/$', batch_download),
    (r'^files/(\w+)$', view_file),
    (r'^files/json/evaluate/$', evaluate),
    (r'^files/json/evaluate/save/$', evaluate_and_save),
    (r'^files/json/(\w+)/$', json_file_display),

    (r'^files/all/json/$', json_all_files),

    (r'^files/all/json_pipelines/$', json_pipelines),
    (r'^files/forms/save_pipeline/$', save_pipeline),

    (r'^files/forms/upload/$', upload_file),
    (r'^files/forms/upload/live/$', upload_file_live),
    (r'^files/forms/delete/$', delete_file),
    (r'^files/pipeline/$', pipeline),
    (r'^files/fitting/(\w+)/$', fitting_request_action),

    #Comment one of these to use the uncommented one: edit-grid is working but no file saving/loading
    #(r'^Alex/edit-grid/', direct_to_template, {'template': 'edit-grid.html'}),
    (r'^Alex/angleCalculator/', direct_to_template, {'template': 'angleCalculator.html'}),

    (r'^files/calcUBmatrix/', calculateUB),
        (r'^files/omegaZero/', runcalc1),
    (r'^files/scatteringPlane/', runcalc2),
    (r'^files/savingData/', makeSaveFile),
    (r'^files/downloadingData/', download_file_angleCalc),
    (r'^files/uploadingData/', upload_file_angleCalc),
)
