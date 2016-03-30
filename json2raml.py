#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import sys
import re
import collections
import traceback

tab = '    '

#===============================================================================
# print_if_key_exists ()
#===============================================================================
def print_if_key_exists(space, dictionary, key):
    if (key in dictionary):
        print '%s%s: %s' % (space, key, dictionary[key])
        return True
    return False

#===============================================================================
# convert ()
#===============================================================================
def convert(data):
    if isinstance(data, basestring):
        return data.encode('utf-8')
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

#===============================================================================
# print_params ()
#===============================================================================
def print_params(dictionary, title):
    print '%s%s:' % (tab*2, title)
    for param in dictionary:
        print '%s%s:' % (tab*3, param['name'])
        print '%stype: %s' % (tab*4, param['type'].lower())
        print_if_key_exists(tab*4, param, 'description')
        print_if_key_exists(tab*4, param, 'example')
        print_if_key_exists(tab*4, param, 'required')

#===============================================================================
# main ()
#===============================================================================
def main():
    if (len(sys.argv) != 2):
        print 'Syntax: %s <file.json>' % sys.argv[0]
        sys.exit(1)
    inputfile = sys.argv[1]

    with open(inputfile) as apisfile:
        apis = json.load(apisfile)
        # Convert all strings to utf8
        apis = convert(apis)
        for api in apis:
            try:
                print '%stitle: %s' % (tab*0, api['name'])
                print '%sbaseUri: %s' % (tab*0, api['endpoints'][0]['host'])
                print '%sversion: %s' % (tab*0, '1.0')
                print '%smashapeUrl: %s' % (tab*0, api['mashape_url'])
                print_if_key_exists(tab*0, api, 'website')
                print_if_key_exists(tab*0, api, 'tags')
                print_if_key_exists(tab*0, api, 'owner')

                for endpoint in api['endpoints']:
                    print '%s%s:' % (tab*0, endpoint['route'])
                    print '%s%s:' % (tab*1, endpoint['method'].lower())
                    print '%sname: %s' % (tab*2, endpoint['name'])  # extra
                    print '%sdescription: %s' % (tab*2, endpoint['description'])

                    # Split url params in query params and uri params
                    uri_param_names = re.findall(r'\{(.*?)\}', endpoint['route'])
                    assert(uri_param_names == [] or 'url_params' in endpoint)
                    uri_params = []
                    query_params = []
                    if ('url_params' in endpoint):
                        if (uri_param_names):
                            uri_params = [ x for x in endpoint['url_params'] if x['name'].lower() in ( x.lower() for x in uri_param_names ) ]
                            query_params = [ x for x in endpoint['url_params'] if x not in uri_params ]
                        else:
                            query_params = endpoint['url_params']

                    if uri_params != []:
                        print_params(uri_params, 'uriParameters')

                    if query_params != []:
                        print_params(query_params, 'queryParameters')

                    if 'payload' in endpoint:
                        print_params(endpoint['payload'], 'bodyBinaryParameters')

                    if 'body_params' in endpoint:
                        print_params(endpoint['body_params'], 'bodyParameters')

                print '========================================================='
            except:
                print '*** ERROR! ***'
                traceback.print_exc(file=sys.stdout)
                print '========================================================='

if __name__ == '__main__':
    main()
