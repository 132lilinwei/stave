from django.contrib import admin
from django.conf import settings
from django.urls import include, path
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.forms import model_to_dict
import uuid
import json
from ..models import Document, User, CrossDocAnnotation
from ..lib.require_login import require_login
import os
import re
from ..apps import read_index_file, pack_index_path
from copy import deepcopy


default_type = "edu.cmu.CrossEventRelation"

def delete_link(textPack, parent_event_id, child_event_id):
    new_links = []
    print(parent_event_id, child_event_id)
    for item in textPack["py/state"]["links"]:
        if item["py/state"]["_parent"]["py/tuple"][1] == parent_event_id and item["py/state"]["_child"]["py/tuple"][1] == child_event_id:
            continue
        new_links.append(item)
    textPack["py/state"]["links"] = new_links


def format_cross_doc_helper(uploaded_link, next_tid):
    link = deepcopy(uploaded_link)
    del link["py/state"]['coref_question_answers']
    del link["py/state"]['suggested_question_answers']

    link["py/object"] = default_type
    link["py/state"]['_tid'] = next_tid
    link["py/state"]["_embedding"] =  []

    # coref
    link["py/state"]["coref_questions"] = {
        "py/object": "forte.data.ontology.core.FList",
        "py/state": {
              "_FList__data": []
        }
    }
    link["py/state"]["coref_answers"] = []
    for item in uploaded_link["py/state"]["coref_question_answers"]:
        link["py/state"]["coref_questions"]["py/state"]["_FList__data"].append(
            {
              "py/object": "forte.data.ontology.core.Pointer",
              "py/state": {
                "_tid": item["question_id"]
              }
            })
        link["py/state"]["coref_answers"].append(item["option_id"])

    #suggested
    link["py/state"]["suggested_questions"] = {
        "py/object": "forte.data.ontology.core.FList",
        "py/state": {
              "_FList__data": []
        }
    }
    link["py/state"]["suggested_answers"] = []
    for item in uploaded_link["py/state"]["suggested_question_answers"]:
        link["py/state"]["suggested_questions"]["py/state"]["_FList__data"].append(
            {
              "py/object": "forte.data.ontology.core.Pointer",
              "py/state": {
                "_tid": item["question_id"]
              }
            })
        link["py/state"]["suggested_answers"].append(item["option_id"])
    return link

def find_and_advance_next_tid(textPackJson):
    textPackJson['py/state']['serialization']["next_id"] += 1
    return textPackJson['py/state']['serialization']["next_id"] - 1


def extract_doc_id_from_crossdoc(cross_doc):
    text_pack = json.loads(cross_doc.textPack)
    doc_external_ids = text_pack["py/state"]["_pack_ref"]
    doc_external_id_0 = doc_external_ids[0]
    doc_external_id_1 = doc_external_ids[1]
    extid_to_name = read_index_file(pack_index_path)
    doc_0 = Document.objects.get(name=extid_to_name[doc_external_id_0])
    doc_1 = Document.objects.get(name=extid_to_name[doc_external_id_1])
    return doc_0, doc_1


def listAll(request):
    crossDocs = CrossDoc.objects.all().values()
    return JsonResponse(list(crossDocs), safe=False)



def query(request, crossDocAnno_id):
    cross_doc = CrossDocAnnotation.objects.get(pk=crossDocAnno_id)
    doc_0, doc_1 = extract_doc_id_from_crossdoc(cross_doc)

    # next_cross_doc = CrossDoc.objects.filter(pk__gt=crossDoc_id).order_by('pk').first()
    # if next_cross_doc == None:
    #     next_cross_doc_id = "-1"
    # else:
    #     next_cross_doc_id = str(next_cross_doc.pk)
    to_return = {"crossDocPack":model_to_dict(cross_doc),"_parent": model_to_dict(doc_0), "_child":model_to_dict(doc_1)}

    return JsonResponse(to_return, safe=False)



# @require_login
# def new_cross_doc_link(request, crossDoc_id):

#     crossDoc = CrossDoc.objects.get(pk=crossDoc_id)
#     docJson = model_to_dict(crossDoc)
#     textPackJson = json.loads(docJson['textPack'])
    

#     received_json_data = json.loads(request.body)
#     link = received_json_data.get('data')
#     print(link)
#     link_id = find_next_tid(textPackJson)
#     link = format_cross_doc_helper(link, link_id)

#     textPackJson['py/state']['links'].append(link)
#     crossDoc.textPack = json.dumps(textPackJson)
#     crossDoc.save()
#     print(link_id)
#     return JsonResponse({"id": link_id}, safe=False)



def new_cross_doc_link(request, crossDocAnno_id):

    crossDoc = CrossDocAnnotation.objects.get(pk=crossDocAnno_id)
    docJson = model_to_dict(crossDoc)
    textPackJson = json.loads(docJson['textPack'])
    

    received_json_data = json.loads(request.body)
    data = received_json_data.get('data')
    link = data["link"]
    print(link)

    link_id = find_and_advance_next_tid(textPackJson)
    link = format_cross_doc_helper(link, link_id)

    # delete possible duplicate link before
    parent_event_id = link["py/state"]["_parent"]["py/tuple"][1]
    child_event_id = link["py/state"]["_child"]["py/tuple"][1]
    delete_link(textPackJson, parent_event_id, child_event_id)

    # append it to the database
    textPackJson['py/state']['links'].append(link)
    crossDoc.textPack = json.dumps(textPackJson)
    crossDoc.save()
    print(link_id)
    return JsonResponse({"crossDocPack": model_to_dict(crossDoc)}, safe=False)


# def update_cross_doc_link(request, crossDocAnno_id):

#     success = False

#     crossDoc = CrossDocAnnotation.objects.get(pk=crossDocAnno_id)
#     docJson = model_to_dict(crossDoc)
#     textPackJson = json.loads(docJson['textPack'])
    

#     received_json_data = json.loads(request.body)
#     data = received_json_data.get('data')
#     link = data["link"]
#     if ("_tid" not in link["py/state"] or link["py/state"]["_tid"] is None):
#         success = False
#     else:
#         for i in range(len(textPackJson['py/state']['links'])):
#             previous_link = textPackJson['py/state']['links'][i]
#             if link['py/state']["_tid"] == previous_link['py/state']["_tid"]:
#                 textPackJson['py/state']['links'][i] = link
#                 crossDoc.textPack = json.dumps(textPackJson)
#                 crossDoc.save()
#                 success = True
#     return JsonResponse({"crossDocPack": model_to_dict(crossDoc), "update_success": success}, safe=False)




def delete_cross_doc_link(request, crossDocAnno_id, link_id):

    crossDoc = CrossDocAnnotation.objects.get(pk=crossDocAnno_id)
    docJson = model_to_dict(crossDoc)
    textPackJson = json.loads(docJson['textPack'])

    deleteIndex = -1
    success = False
    for index, item in enumerate(textPackJson['py/state']['links']):
        if item["py/state"]['_tid'] == link_id:
            deleteIndex = index
            success = True
            
    if deleteIndex == -1:
        success = False
    else:
        del textPackJson['py/state']['links'][deleteIndex]
        crossDoc.textPack = json.dumps(textPackJson)
        crossDoc.save()

    return JsonResponse({"crossDocPack": model_to_dict(crossDoc), "update_success": success}, safe=False)

