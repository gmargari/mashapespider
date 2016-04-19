#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import print_function
import json
import sys
import re
import collections
import traceback

tab = '    '
type_map = {
    "JSON": "application/json",
    "XML": "application/xml",
    "TEXT": "text/plain",
    "BINARY": "binary/octet-stream",
}

#===============================================================================
# print_if_key_exists ()
#===============================================================================
def print_if_key_exists(space, dictionary, key):
    if (key in dictionary):
        print('%s%s: %s' % (space, key, dictionary[key]))
        return True
    return False

#===============================================================================
# convert ()
#===============================================================================
def convert(data):
    if isinstance(data, basestring):
        d = data.encode('utf-8')
        d = d.replace("&lt;", "<").replace("&gt;", ">")
        d = d.replace("&nbsp;", " ").replace("&amp;", "&")
        return d
    elif isinstance(data, collections.Mapping):
        return dict(map(convert, data.iteritems()))
    elif isinstance(data, collections.Iterable):
        return type(data)(map(convert, data))
    else:
        return data

#===============================================================================
# print_api_header ()
#===============================================================================
def print_api_header():
    print('#%RAML 0.8')
    print('')

#===============================================================================
# print_api_footer ()
#===============================================================================
def print_api_footer():
    print('=========================================================')

#===============================================================================
# print_api_description ()
#===============================================================================
def print_api_description(api):
    print('%stitle: %s' % (tab*0, api['name']))
    print('%sbaseUri: %s' % (tab*0, api['endpoints'][0]['host']))
    print('%sversion: %s' % (tab*0, '1.0'))
    print('%smashapeUrl: %s' % (tab*0, api['mashape_url']))
    print_if_key_exists(tab*0, api, 'website')
    print_if_key_exists(tab*0, api, 'tags')
    print_if_key_exists(tab*0, api, 'owner')

#===============================================================================
# print_endpoint_description ()
#===============================================================================
def print_endpoint_description(endpoint):
    print('')
    print('%s%s:' % (tab*0, endpoint['route']))
    print('%s%s:' % (tab*1, endpoint['method'].lower()))
    print('%sdisplayName: %s' % (tab*2, endpoint['name']))  # extra
    print('%sdescription: %s' % (tab*2, endpoint['description']))

#===============================================================================
# print_endpoint_response ()
#===============================================================================
def print_endpoint_response(endpoint):
    if ('response' in endpoint):
        rcode, rtype = endpoint['response'].split(" / ")
        print('%sresponses:' % (tab*2))
        print('%s%s:' % (tab*3, rcode))
        print('%sbody:' % (tab*4))
        print('%s%s:' % (tab*5, type_map[rtype]))
        if ("response_example" in endpoint):
            print('%sexample:' % (tab*6))
            # Print each line of endpoint['response_example'] in a separate
            # line with tabs before it
            for line in endpoint['response_example'].split("\n"):
                print('%s%s' % (tab*7, line))

#===============================================================================
# print_params ()
#===============================================================================
def print_params(dictionary, title):
    if len(dictionary) > 0:
        print('%s%s:' % (tab*2, title))
        for param in dictionary:
            print('%s%s:' % (tab*3, param['name']))
            print('%stype: %s' % (tab*4, param['type'].lower()))
            print_if_key_exists(tab*4, param, 'description')
            print_if_key_exists(tab*4, param, 'example')
            print_if_key_exists(tab*4, param, 'required')

#===============================================================================
# main ()
#===============================================================================
def main():
    if (len(sys.argv) != 2):
        print('Syntax: %s <file.json>' % sys.argv[0])
        sys.exit(1)
    inputfile = sys.argv[1]

    with open(inputfile) as apisfile:
        apis = json.load(apisfile)
        # Convert all strings to utf8
        apis = convert(apis)
        for api in apis:
            try:
                # No endpoints, probably url was not parsed properly (e.g. page wasn't fully loaded when parsing started)
                if ('endpoints' not in api or api['endpoints'] == []):
                    continue

                print_api_header()
                print_api_description(api)

                for endpoint in api['endpoints']:
                    print_endpoint_description(endpoint)

                    # Split url params in query params and uri params
                    uri_param_names = re.findall(r'\{(.*?)\}', endpoint['route'])
                    uri_params = []
                    query_params = []
                    if ('url_params' in endpoint):
                        if (uri_param_names):
                            uri_params = [ x for x in endpoint['url_params'] if x['name'].lower() in ( x.lower() for x in uri_param_names ) ]
                            query_params = [ x for x in endpoint['url_params'] if x not in uri_params ]
                        else:
                            query_params = endpoint['url_params']
                    assert(uri_param_names == [] or len(uri_param_names) == len(uri_params))

                    body_params = endpoint['body_params'] if 'body_params' in endpoint else []
                    payload_params = endpoint['payload'] if 'payload' in endpoint else []

                    print_params(uri_params, 'uriParameters')
                    print_params(query_params, 'queryParameters')
                    print_params(payload_params, 'bodyBinaryParameters')  ## *** ## *** ## *** ## *** ## *** ##
                    print_params(body_params, 'body')

                    print_endpoint_response(endpoint)

                    if ('response' not in endpoint and endpoint['method'] == "GET"):
                        print('\n*** WARNING: %s ***' % (api['mashape_url']), file=sys.stderr)
                        print('method for %s is GET but no response defined' % (endpoint['route']), file=sys.stderr)

                print_api_footer()
            except:
                print('*** ERROR: ***')
                print('=========================================================')
                print('\n*** ERROR: %s ***' % (api['mashape_url']), file=sys.stderr)
                traceback.print_exc()

if __name__ == '__main__':
    main()
