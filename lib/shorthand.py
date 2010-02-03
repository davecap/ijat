from pyparsing import *
import string
# import sys

def main():
    print 'This is a library!'

def test_parse_shorthand():
    test_cases = [  ['', None],
                    ['hot dog @ la riviera', {'food': 'hot dog', 'comment': None, 'cost': 0, 'place': 'la riviera', 'rating': 0}],
                    ['1 dynamite ham @ my mother\'s house *** $$ it was amazing!', {'food': '1 dynamite ham', 'rating': 3, 'cost': 2, 'place': "my mother's house", 'comment': 'it was amazing!'}],
                    ['2x hamburgers! @ la belle province * $ not so good...', {'food': '2x hamburgers!', 'rating': 1, 'cost': 1, 'place': 'la belle province', 'comment': 'not so good...'}],
                    ['2x hamburgers! @ la belle province $ * not so good...', {'food': '2x hamburgers!', 'rating': 1, 'cost': 1, 'place': 'la belle province', 'comment': 'not so good...'}],
                    ['2x hamburgers!la belle province so good...', None],
                    ['pizza @ bitondos $ ** so good', {'food': 'pizza', 'rating': 2, 'cost': 1, 'place': 'bitondos', 'comment': 'so good'}]
                ]
    for t in test_cases:
        assert parse_shorthand(t[0]) == t[1]

def parse_shorthand(shorthand):
    # useful types
    integer = Word( nums )
    dot = Literal(".")
    at = Literal("@").suppress()
    star = Literal("*")
    dollar = Literal("$")
    
    okchars = alphanums+"'\"[]{}()-_=+&^%#!`~><.,?/;:|\\"
    
    # shorthand elements
    text = OneOrMore( Word( okchars ) )
    
    food = Group(text).setResultsName('food')
    place = Group(text).setResultsName('place')
    comment = Group(text).setResultsName('comment')
    rating = OneOrMore( star ).setResultsName('rating')
    cost = OneOrMore( dollar ).setResultsName('cost')
    
    properties = rating ^ cost
    
    # allows for mixup of rating/cost order
    # <food> @ <place> [****] [$$$$] [comment] 
    bnf = food + at + place + ZeroOrMore(properties) + Optional(comment)
    
    try:
        parsed_shorthand = bnf.parseString(shorthand)
        cleaned_shorthand = parsed_shorthand.asDict()
        cleaned_shorthand['food'] = " ".join(cleaned_shorthand['food'])
        cleaned_shorthand['place'] = " ".join(cleaned_shorthand['place'])
        
        if 'comment' in cleaned_shorthand:
            cleaned_shorthand['comment'] = " ".join(cleaned_shorthand['comment'])
            if cleaned_shorthand['comment'] == '':
                cleaned_shorthand['comment'] = None
        else:
            cleaned_shorthand['comment'] = None
        if 'rating' in cleaned_shorthand:
            cleaned_shorthand['rating'] = len(cleaned_shorthand['rating'])
            if cleaned_shorthand['rating'] > 5:
                cleaned_shorthand['rating'] = 5
        else:
            cleaned_shorthand['rating'] = 0
        if 'cost' in cleaned_shorthand:
            cleaned_shorthand['cost'] = len(cleaned_shorthand['cost'])
            if cleaned_shorthand['cost'] > 3:
                cleaned_shorthand['cost'] = 3
        else:
            cleaned_shorthand['cost'] = 0
    except ParseException, e:
        #print e
        return None
    else:
        return cleaned_shorthand
    
if __name__=='__main__':
    main()