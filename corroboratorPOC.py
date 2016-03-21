from subprocess import *
import re
import treetaggerwrapper
import sparqlQuerypy
from bs4 import BeautifulSoup

CONSTANTKEYVERBS="die, died, death, born, birth, sworn in" #Set of words that if present in the sentence, then don't discard the sentence, we are interested.
tagger = treetaggerwrapper.TreeTagger(TAGLANG = 'en', TAGDIR = '/home/vedu29/python/Gsoc/treetagger')


def jarWrapper(*args): # The helper function to use the jar file.
    process = Popen(['java', '-jar']+list(args), stdout=PIPE, stderr=PIPE)
    ret=[]
    while process.poll() is None:
        line = process.stdout.readline()
        if line != '' and line.endswith('\n'):
            ret.append(line[:-1])
        stdout, stderr = process.communicate()
        ret += stdout.split('\n')
        if stderr != '':
            ret += stderr.split('\n')
        ret.remove('')
        return ret

def returnProperty(word): #helper function to map the verb to a property. This will be small considering the number of date properties in DBpedia.
    if word in ['death', 'die']: return 'http://dbpedia.org/ontology/deathDate'
    if word in ['birth', 'born', 'bear']: return 'http://dbpedia.org/ontology/birthDate'


def normalizeAnnotations(sentence): # helper function to remove the references annotation, that appear as square brackets at the end of the sentence.
    return re.sub(r'\[[0-9]*\]', ' ', sentence)

def sentenceSplitter(sentence): # helper regular function to correctly find end of sentences.
    return re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', sentence)
    
def normaliseResult(result):
    normRes=[]
    for sentence in result:
        sent=normalizeAnnotations(sentence)
        normRes += sentenceSplitter(sent)
    return normRes

def findAndGenericAnnotateTime(sentence): #Replacing heidelTime tagged Timex tags to a generic 'TIME' so that treeTagger can work its magic without hiccups.
    return re.sub('<TIMEX3((?!<TIMEX3).)*</TIMEX3>', 'TIME', sentence)

def treetag(sentence, encoding = None): # TreeTagger helper function.
    if encoding != None:
        return treetaggerwrapper.make_tags(tagger.tag_text(unicode(sentence, "utf-8")))
    else:
        return treetaggerwrapper.make_tags(tagger.tag_text(sentence))

def returnKeyverbs(): #formats the key verbs above.
    return '|'.join(verb for verb in CONSTANTKEYVERBS.split(', '))


def findSubVerbsTime(tagsentence): # The main helper function that figures out the subject in the sentence and finds the correct core verbs marked by an '*'
    pos=[]
    pos2=[]
    seenSubject=False
    seenVerb=False
    lastfew=0
    for i, tags in enumerate(tagsentence):
        if tags.pos=='NP' or tags.pos=='PP':
            pos += [tags.word]
            seenSubject=True
            lastfew+=1
        if re.match(u'V..|V.', tags.pos) != None and seenSubject:
            if not seenVerb:
                subject = pos[-lastfew:]
                pos2 += [[subject]]
            if re.match(u'VB.', tags.pos) != None:
                pos2[-1] += [tags.word]
            else:
                pos2[-1] += [tags.word+'*']
                seenVerb=True
        if re.match(u'V..|V.', tags.pos) == None and seenVerb:
            seenVerb=False
            seenSubject=False
            lastfew=0
    return pos2

def lemmatizeMainVerb(item):
    for verb in item[1:]:
        if '*' in verb:
            return treetag(verb)[0].lemma


def listTimes(sentence):
    soup = BeautifulSoup(sentence, 'html.parser')
    return soup.find_all('timex3')


def main(args):
    result = jarWrapper(*args)
    for sentence in normaliseResult(result):
        
        sent=findAndGenericAnnotateTime(sentence)
    
        m = re.match(r"(?P<first_part>.*) (?P<predicate>%s) (?P<second_part>.*)"%(returnKeyverbs()), sent)
        if m!=None:       

            left=treetag(m.group('first_part'), "utf-8")
            middle=treetag(m.group('predicate'), "utf-8")
            right=treetag(m.group('second_part'), "utf-8")
            tagsentence = left + middle + right

            if 'TIME' in m.group('first_part') or 'TIME' in m.group('second_part'):#  Here onwards is to find the subject and verb

                subVerbTime = findSubVerbsTime(tagsentence)
                for item in subVerbTime:
                    subject=" ".join(thing for thing in item[0])
                    if subject.lower() in ['he','she', 'it']:
                        subject=previousSubject
                    annotate = sparqlQuerypy.findAnnotation(subject)
                    annotatedSubject = annotate[0]['s']['value']
                    previousSubject = subject
                    verbLemma=lemmatizeMainVerb(item)
                    if verbLemma != None: prop=returnProperty(verbLemma)

                timexList = listTimes(sentence)

                i=0
                while timexList[i]['type']not in ["DATE","TIME"]:
                    i+=1
                time= timexList[i]['value']
                date= sparqlQuerypy.findDate(annotatedSubject, prop)
                if len(date) != 0:
                    date= date[0]['z']['value']
                    print '- - - - - - - - - - - - - - - - \n \n'
                    print sentence
                    print '     '
                    print 'The subject is:', subject
                    print 'The annotated subject is:', annotatedSubject
                    print 'The property is:', prop
                    print 'Date according to dbpedia:', date
                    print 'Date mined from the text:', time
                    print '\n \n'

if __name__=='__main__':
    args = ['de.unihd.dbs.heideltime.standalone.jar', 'input']
    result = jarWrapper(*args)
    tagger = treetaggerwrapper.TreeTagger(TAGLANG = 'en', TAGDIR = '/home/vedu29/python/Gsoc/treetagger')
    
    main(args)
            

            
    
