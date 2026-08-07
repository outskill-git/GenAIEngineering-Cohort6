# Required Imports
from sqlalchemy import inspect, text, create_engine
import csv
import io
import dotenv
from groq import Groq
import json
import re
import os

## Inputs
table_name = 'Student_Performance'
Prompt = "Tell me the lowest 5 scorers, despite of having parents having done Bachelor"
# Prompt = "Tell me who are the students having attendance below 60"
# Prompt = "Tell me number of students based on their internet quality types"

DB_File = "Sample_2 copy.db"

if os.path.exists (DB_File):
    sql_engine = create_engine("sqlite:///"+DB_File)
    conn = sql_engine.connect ()
else:
    print ("\n DB Files does not exist")
    exit ()

# LLM Client
dotenv.load_dotenv ()
G_client = Groq()
# G_client = Groq(api_key="Your Key")
G_Model = "llama-3.3-70b-versatile"

def get_table_schema_as_csv(connection, table_name):
    """
    This function provides Table schema of a SQL table as CSV formatted string.
    It provides 3 columns. Its the Column_Name, Type, Sample_Data from the table
    It takes input as sqlalchemy connection and table name
    """

    # Fetch column title
    inspector = inspect(connection)
    columns = inspector.get_columns(table_name)

    # Fetch first row as sample content
    sample_query = text(f"SELECT * FROM {table_name} LIMIT 1")
    result = connection.execute(sample_query)
    first_row = result.mappings().fetchone()

    # Prepare CSV output
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Column_Name', 'Type', 'Sample_Content'])

    for col in columns:
        name = col['name']
        type_ = str(col['type'])
        sample = first_row[name] if first_row else None
        writer.writerow([name, type_, sample])

    return output.getvalue()

def extract_sql_query(text):
    """
    Extracts SQL query string from a block of text enclosed.
    Eg.  ```sql ... ```, '''sql ... '''
    """
    # Match common SQL code block styles
    pattern = r"(?:```sql|'''sql|```|''')\s*(.*?)\s*(?:```|'''|$)"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()
    else:
        return text.strip()  # it's just raw SQL

def RAG_Response (Client, Model, conn, table_name, Prompt) :

    ## For a User prompt, get the SQL query to be raised.
    # Get the table schema with sameple data (CSV format)
    # Pass this schema and user prompt to LLM to get the SQL Qeury as response
    Q_Instr = " Required Output:\
                SQL Query String.\n\
                Instructions:\
                From the given SQL table schema, formulate SQL query which answers user's question.\
                Write query to retrieve all relevant information to provide enough context for the question.\
                Provide just the query string. No title, no introduction\
                Its SQLite DB. Schema is provided as comma seperated text.\
                When you use Text fields, always bring to lower case and use wild card : %xxx%\
                If question is not relevant to schema, say 'No relevant data'.\
                "

    Schema = get_table_schema_as_csv (conn, table_name)
    # print (Schema)

    messages=[
        {
            "role": "system",
            "content": Q_Instr
        },

        {
            "role": "user",
            "content": f"Table Name : {table_name} \n"+"Schema :\n"+Schema+"\n Question : \n"+Prompt
        }
    ]
    completion = Client.chat.completions.create(
        messages=messages,
        model=Model,
        # temperature=0.0

    )

    ## Get the query string
    Query_String = completion.choices[0].message.content
    # print (Query_String)

    Query_String = extract_sql_query (Query_String)
    print (Query_String)

    #Fetch the data from DB
    result = conn.execute (text(Query_String))

    # Query output into JSON
    rows = [row._asdict () for row in result]
    json_output = json.dumps(rows,  indent=2)
    # print (json_output)

    # Basic Response generation Instruction
    R_Instr = "Using the context given, provide response to the user question or statement.\
                The required data is provided to you as context. Formulate the answer from this.\
                Answer to the question with required details"

    # Contextual Instruction for Response Generation
    # R_Instr = f"User had asked : {Prompt}."\
    #            "Further based on the user query, relevant data is retrived from database and presented as context below."\
    #            "Conisdering the fact that its a filtered data that is relevant to answer the query, Respond to the question."\
    #            "Provide your response with details and description."\
    #            "Respond naturally to the question. Don't explain the mechanism how did you arrive at answer"

    messages=[
        {
            "role": "system",
            "content": R_Instr
        },

        {
            "role": "user",
            "content":"Context : \n"+ json_output + "Query : \n" + Prompt
        }
    ]
    completion = Client.chat.completions.create(
        messages=messages,
        model=Model,
    )

    Response = completion.choices[0].message.content
    return Response

## invoke the RAG pipeline for a run
G_Response = RAG_Response (G_client, G_Model, conn, table_name, Prompt)
print (G_Response)
