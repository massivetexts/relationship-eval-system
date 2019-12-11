from flask import Flask, request, send_from_directory
import pandas as pd
import json
from htrc_features import utils
import time
import glob

app = Flask(__name__)

def css_escape(htid): 
    return (utils.clean_htid(htid).replace('.', '-A')
            .replace('$', '-B').replace(',', '-C')
            .replace('+', '-D').replace('=', '-E')
            .replace('_', '-F')
           )

def id_decode(htid):
    return htid.replace("+", ":").replace("=", "/").replace(",", ".")

def css_unescape(htid):
    unescaped = (htid.replace('-A', '.').replace('-B', '$')
                 .replace('-C', ',').replace('-D', '+')
                 .replace('-E','=').replace('-F','_')
                )
    return id_decode(unescaped)

def get_htid_list():
    files = glob.glob(app.root_path + '/data/*')
    clean_htids = [file.split('data/')[1].replace('.json', '') for file in files]
    return [id_decode(htid) for htid in clean_htids]

def request_as_df(batch):
    rows = []
    timestamp = time.time() 
    candidates = [key for key in batch.keys() if key.startswith('judgment')]

    for field in ['name', 'targetId']:
        if field not in batch:
                batch[field] = None
   
    for candidate in candidates:
        chtid = css_unescape(candidate.replace('judgment-', ''))
        notesid = candidate.replace('judgment-', 'notes-')
        if notesid not in batch:
            batch[notesid] = None
        row = { 'rater': batch['name'], 
               'target': batch['targetId'], 
               'candidate': chtid, 
               'judgment': batch[candidate],
               'notes': batch[notesid],
               'timestamp': timestamp
              }
        rows.append(row)

    df = pd.DataFrame(rows)[['rater', 'target', 'candidate', 'judgment', 'notes', 'timestamp']]
    return df

def rating_url(htid, rater=None):
    try:
        css_htid = css_escape(htid)
    except:
        css_htid = htid
    url = "rating?htid={}".format(css_htid)
    if rater:
        url += "&name={}".format(rater)
    return url

def get_target_counts(rater_targets):
    target_counts = rater_targets.target.value_counts()
    htids = get_htid_list()
    no_ratings = [htid for htid in htids if htid not in target_counts.index]
    no_ratings = pd.Series([0] * len(no_ratings), index=no_ratings)
    target_counts = target_counts.append(no_ratings).sort_values()
    return target_counts

def print_target_counts(rater_targets, rater=None, n=1000):
    target_counts = get_target_counts(rater_targets)
    if rater:
        done_by_rater = rater_targets[rater_targets['rater'] == rater].target
        target_counts = target_counts[~target_counts.index.isin(done_by_rater)]

    li = "<ol>"
    for htid,n in target_counts.iloc[:n].iteritems(): 
        li += "<li><a href='{}'>{}</a> - Times rated: {}</li>".format(rating_url(htid, rater=rater), htid, n)
    li += "</ol>"
    return li

def print_recently_rated(rater_targets, n=5):
    return rater_targets.sort_values('timestamp', ascending=False).head(n).to_html()
    
def load_results(pathglob='results/results.*.csv', drop_duplicates=True):
    colnames = ['rater', 'target', 'candidate', 'judgment', 'notes', 'timestamp']
    try:
        all_df = [pd.read_csv(path, names=colnames) for path in glob.glob(app.root_path + '/' + pathglob)]
        df = pd.concat(all_df)
    except:
        df = pd.DataFrame([], columns=colnames)
    if drop_duplicates:
        df = df.drop_duplicates()
    rater_targets = df[['rater', 'target', 'timestamp']].drop_duplicates(['rater', 'target'])
    return (df, rater_targets)
    
def global_stats():
    pass

def print_rater_counts(rater_targets):
    return (rater_targets.rater.value_counts()
            .reset_index().rename(columns={'index':'rater'})
            .to_html()
           )

@app.route("/submit")
def submit():
    input = dict(request.args.items())
    name = request.args.get('name')
    response = ""
    if len(input) > 1:
        try:
            formatted = request_as_df(input)
            formatted.to_csv(app.root_path + '/results/results.0.csv', mode='a', header=False)
            response += "Submitted! Below is the data you submitted. "
            response += "If you need something fixed later, you can save this for reference:<hr />"
        except IOError:
            response += "<h1>IO Error. Dr. O screwed something up, let him know.</h1>"
        except:
            response += "<h1>Nothing submitted due to error.</h1>If unexpected,"
            response += "</h1>Save this string somewhere for Dr. O to inspect:<br/>"
        response += "<textarea>{}</textarea>".format(input)
        
    df, rater_targets = load_results()  
        
    response += "<hr /><h2>More to rate</h2>"
    response += print_target_counts(rater_targets, rater=name, n=15)
    
    response += "<hr /><h2>How much have you rated?</h2>"
    response += print_rater_counts(rater_targets)

    response += "<hr /><h2>Recently Rated</h2>"
    response += print_recently_rated(rater_targets)
    
    return response

@app.route("/")
def stats():
    name = request.args.get('name')
    response = "<h1>Info</h1>"
    
    df, rater_targets = load_results()
    
    response += "<hr /><h2>More to rate</h2>"
    response += print_target_counts(rater_targets, rater=name, n=15)
    
    response += "<hr /><h2>How much have you rated?</h2>"
    response += print_rater_counts(rater_targets)

    response += "<hr /><h2>Recently Rated</h2>"
    response += print_recently_rated(rater_targets)
    
    return response
    

@app.route("/rating")
def rating():
    return app.send_static_file("rating.html")

@app.route('/data/<path:path>')
def send_data(path):
    return send_from_directory('data', path)

@app.route('/js/<path:path>')
def send_js(path):
    return send_from_directory('static/js', path)

@app.route('/css/<path:path>')
def send_css(path):
    return send_from_directory('static/css', path)
    
if __name__ == "__main__":
    app.run(debug=True)
