# JSON Mapping

The `JsonMapper` class is a tool for translating/converting a JSON document into another JSON document with a 
different structure. The mapping process follows a dictionary-based specification of how fields map to the new 
JSON format. The main function in the `JsonMapper` is `map` that takes a structured specification:

        JsonMapper(json_document).map(specification)


## Mapping Specification

The general idea is that the specification describes the resulting structure of the converted JSON document. The
dictionary-based specification will closely resemble the schema of the resulting JSON.

### Field Specification

A field specification is defined by a list of parameters, the first of which is a name that refers to a field in 
the current JSON to be converted. This is the only required field.

        <converted_field>: [<original_field>]

For example, given the sample JSON document,

        {
            "person_name": "Juan dela Cruz"
            "person_age": 37 
        }

the simplest mapping that can be done is to translate to a different field name. For example, to map 
`person_name` to `name` in the resulting JSON, the following specification is used:

        {
            'name': ['person_name']
        }

#### Field Chaining

JSON mapping also supports chaining of fields on either or both side of the specification. For example, using the
following specification to the JSON above,

        {
            'person.name': ['person_name'],
            'person.age': ['person_age']
        }
 
 will result in the conversion:
 
        {
            "person": {
                "name": "Juan dela Cruz",
                "age": 37
            }
        }
        
 To convert back to the original JSON in the example, just reverse the field specification, for example, 
`'person_name': ['person.name']`. Field chaining can be done on multiple levels. However, at the time of writing, 
`JsonMapper` does not support direct field chaining for JSON array types. Processing such fields can be expressed 
through [anchoring](#anchoring) and [nesting](#nested-specification).
 
#### Post-Processing Using Generic Functions

The JSON mapper allows post processing of field values for more complex translation rules. This is done by 
specifying a generic Python function that takes an arbitrary list of arguments (`*args`). The post-processing 
function is specified after the original field name in the field specification:

        <converted_field>: [<original_field>, <post_processor>{, <args>*}]
        
`JsonMapper` will pass the value of the specified field as the first argument to the post-processor. Taking the 
same example in the previous section, a boolean field `adult` can be added using this feature. The following spec
demonstrates how this can be done:
            
        {
            'name': ['person_name'],
            'age': ['person_age'],
            'adult': ['person_age', is_adult]
        }
        
with the post-processor defined as:

        def is_adult(*args):
            age = args[0]
            return age >= 18
            
At the time of writing, there are a few built-in post-processors that can be applied to some common use-cases like
defaulting values (`default_to`), concatenating lists (`concatenate_list`), etc. These can be found in 
`post_process.py` module.

### Anchoring

While the `JsonMapper` has support for field chaining, for complex JSON with several levels of nesting, 
combined with long field names and field list, repetitively providing full field chain can be tedious. To be able
to express this more concisely, anchoring can be used. Anchoring specifies the root of the JSON structure to 
map to a new JSON format.

#### The `on` Parameter

The `map` function in the `JsonMapper` takes a parameter named `on` that can be used to specify the root of the
JSON on which to start mapping. For example, given the following JSON,

        {
            "user": {
                "settings": {
                    "basic": {...},
                    "advanced": {
                        "security": {
                            "javascript_enabled": true,
                            "allow_trackers": false
                        }
                    }
                }
            }
        }
 
 the processing can be anchored on `user.settings.advanced.security` to translate the security settings. The
 following specification,
  
        {
            'javascript': ['javascript_enabled'],
            'trackers': ['allow_trackers']
        }

applied to the JSON above using `map(specification, on='user.settings.advanced.security')`, will result in,

        {
            "javascript": true,
            "trackers": false
        }

#### The `$on` Specification

#### Chaining `on` and `$on`
        
### Nested Specification

#### Filtering