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
 `'person_name': ['person.name']`.

### Anchoring
        
### Nested Specification