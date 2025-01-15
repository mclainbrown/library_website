import pandas as pd
import requests
from flask import Flask, render_template, request
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import DC

app = Flask(__name__)

# New CSV URL (change this URL if needed)
CSV_URL = 'https://raw.githubusercontent.com/mclainbrown/mclainbrown/refs/heads/main/Untitled%20spreadsheet%20-%20Sheet1.csv'


# Load the CSV data
def load_data():
    response = requests.get(CSV_URL)
    if response.status_code == 200:
        from io import StringIO
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)

        # Clean up column names (strip any leading/trailing spaces)
        df.columns = df.columns.str.strip()

        # Print the column names to verify
        print("CSV Columns after cleaning:", df.columns)

        return df
    else:
        return pd.DataFrame()


# Load the data globally for the app
artists_df = load_data()

# Create an RDF graph and namespace
kd = Namespace("http://www.kpopdictionary.com/")
g = Graph()

# Add RDF triples based on the artist data in the DataFrame
for index, row in artists_df.iterrows():
    subject = URIRef(kd[str(row['artist'])])
    g.add((subject, DC.creator, URIRef(kd[str(row['company'])])))
    g.add((subject, DC.date, Literal(row['debut_year'])))


# Function to get RDF data for a specific artist
def get_artist_rdf(artist_name):
    artist_uri = URIRef(kd[artist_name])
    artist_graph = Graph()

    # Get all triples related to this artist
    for s, p, o in g.triples((artist_uri, None, None)):
        artist_graph.add((s, p, o))

    return artist_graph.serialize(format='turtle')


@app.route('/', methods=['GET', 'POST'])
def index():
    search_results = []

    if request.method == 'POST':
        search_term = request.form['search']

        # Ensure that 'artist' column exists before performing search
        if 'artist' in artists_df.columns:
            search_results = artists_df[artists_df['artist'].str.contains(search_term, case=False, na=False)]
        else:
            print("Error: 'artist' column not found!")

    # Check if search_results is an empty DataFrame or list
    is_empty = search_results.empty if isinstance(search_results, pd.DataFrame) else len(search_results) == 0

    # If the user has selected an artist, get their RDF data
    artist_rdf = None
    if isinstance(search_results, pd.DataFrame) and search_results.shape[
        0] == 1:  # Only get RDF if exactly one artist is found
        artist_name = search_results.iloc[0]['artist']
        artist_rdf = get_artist_rdf(artist_name)

    return render_template('index.html', search_results=search_results, is_empty=is_empty, artist_rdf=artist_rdf)


if __name__ == '__main__':
    app.run(debug=True)
