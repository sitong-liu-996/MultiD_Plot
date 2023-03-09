import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import plotly.express as px
import base64
import io

# Define app
app = dash.Dash(__name__)
server = app.server
app.config['suppress_callback_exceptions'] = True

# Define options for sample dropdown
sample_options = []
dye_combination = ['C40_FAM', 'C40_VIC', 'C40_ABY', 'C40_JUN', 'C40_ROX']
# Define layout
app.layout = html.Div([
    html.H1("Parallel Coordinate and 2D Plot", style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select partition_summary_table.csv')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '0px 20px',
            'fontSize': '20px'
        },
        multiple=False
    ),

    html.Div(id='output-data-upload'),

    html.Div([
        html.Div([
            html.Label("Select Sample:", style={'fontSize': '24px', 'textAlign':'center', 'margin': '0 20px'}),
            dcc.Dropdown(
                id='sample-dropdown',
                options=sample_options,
                value='A1'
            )
        ], style={'width': '30%', 'display': 'inline-block', 'marginRight': '500px'}),

        html.Div([
            html.Label("Select Dye Combination For Scatter Plot:",
                       style={'fontSize': '24px', 'textAlign': 'center', 'margin': '0 20px'}),
            dcc.Dropdown(id='Dye-Combination-Dropdown',
                         options=[
                             {'label': 'FAM - VIC', 'value': 'FAM_VIC'},
                             {'label': 'FAM - ABY', 'value': 'FAM_ABY'},
                             {'label': 'FAM - JUN', 'value': 'FAM_JUN'},
                             {'label': 'FAM - ROX', 'value': 'FAM_ROX'},
                             {'label': 'VIC - ABY', 'value': 'VIC_ABY'},
                             {'label': 'VIC - JUN', 'value': 'VIC_JUN'},
                             {'label': 'VIC - ROX', 'value': 'VIC_ROX'},
                             {'label': 'ABY - JUN', 'value': 'ABY_JUN'},
                             {'label': 'ABY - ROX', 'value': 'ABY_ROX'},
                             {'label': 'JUN - ROX', 'value': 'JUN_ROX'}
                         ],
                         value='FAM_VIC', searchable=True
                         )
        ], style={'width': '30%', 'display': 'inline-block'}),
    ], style={'marginBottom': '20px', 'marginTop': '20px'}),

    html.Div(id='selected-count', style={'fontSize': '24px', 'textAlign': 'center'}),

    html.Div([html.Label("Selected Data Point Labeling:",
                         style={'fontSize': '24px', 'textAlign': 'center', 'margin': '0 20px'}),
              dcc.Dropdown(id='label-dropdown',
                           options=[
                               {'label': 'Selected FAM Data Points Label as Positive', 'value': 'FAM_labeling_Pos'},
                               {'label': 'Selected VIC Data Points Label as Positive', 'value': 'VIC_labeling_Pos'},
                               {'label': 'Selected ABY Data Points Label as Positive', 'value': 'ABY_labeling_Pos'},
                               {'label': 'Selected JUN Data Points Label as Positive', 'value': 'JUN_labeling_Pos'},
                               {'label': 'Selected FAM Data Points Label as Negative', 'value': 'FAM_labeling_Neg'},
                               {'label': 'Selected VIC Data Points Label as Negative', 'value': 'VIC_labeling_Neg'},
                               {'label': 'Selected ABY Data Points Label as Negative', 'value': 'ABY_labeling_Neg'},
                               {'label': 'Selected JUN Data Points Label as Negative', 'value': 'JUN_labeling_Neg'},
                           ],
                           value=None, searchable=True,
                           placeholder='Select a labeling'
                           )
              ], style={'width': '30%', 'marginBottom': '20px'}),

    html.Div(id='selected-points-table'),

    dcc.Graph(id='2d-plot'),

    dcc.Graph(id='parallel-plot')
])


# Define callback for uploading CSV file
@app.callback(Output('output-data-upload', 'children'),
              Output('sample-dropdown', 'options'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'))
def update_output(contents, filename):
    global sample_options, df
    if contents is not None:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename:
                # Assume that the user uploaded a CSV file
                orig_data = pd.read_csv(
                    io.StringIO(decoded.decode('utf-8')))
            elif 'xls' in filename:
                # Assume that the user uploaded an Excel file
                df = pd.read_excel(io.BytesIO(decoded))
        except Exception as e:
            print(e)
            return html.Div([
                'There was an error processing this file.'
            ])

        df1 = orig_data[['Run', 'Sample', 'Index', 'Reject', 'Channel', 'C40']]
        df2 = df1[df1['Reject'] == False]
        df3 = df2.set_index(['Run', 'Sample', 'Index', 'Channel'])[
            'C40'].unstack().add_prefix('C40_').rename_axis([None],
                                                            axis=1).reset_index()
        df = df3.reindex(
            ['Sample', 'C40_FAM', 'C40_VIC', 'C40_ABY', 'C40_JUN', 'C40_ROX'],
            axis=1)
        # create new columns with default value of Neg
        new_cols = pd.DataFrame({
            'FAM_labeling': ['Neg'] * len(df),
            'VIC_labeling': ['Neg'] * len(df),
            'ABY_labeling': ['Neg'] * len(df),
            'JUN_labeling': ['Neg'] * len(df)
        })
        df = pd.concat([df, new_cols], axis=1)

        sample_options = [{'label': s, 'value': s} for s in df['Sample'].unique()]
        return html.Div([
            html.H5('Uploaded: {}'.format(filename), style={'fontSize': '18px'}),
            html.Hr(),
            html.P('Run Name: {}'.format(orig_data['Run'].unique()), style={'fontSize': '24px'}),
            #html.P('Number of rows: {}'.format(len(df)), style={'fontSize': '18px'}),
            #html.P('Number of columns: {}'.format(len(df.columns)), style={'fontSize': '18px'}),
            #html.P('Column Name: {}'.format(df.columns), style={'fontSize': '18px'})
        ]), sample_options
    else:
        df = pd.DataFrame()
        return html.Div()

# define the callback to update the selected points table
@app.callback(
    dash.dependencies.Output('selected-points-table', 'children'),
    dash.dependencies.Input('2d-plot', 'selectedData'),
    dash.dependencies.Input('label-dropdown', 'value'),
    dash.dependencies.State('selected-points-table', 'children'),
    Input('sample-dropdown', 'value')
)
def update_selected_points_table(selected_data, labeling, existing_table, selected_sample):
    # create a Dash HTML table component from the DataFrame
    table_rows = []
    for col in ['FAM_labeling', 'VIC_labeling', 'ABY_labeling', 'JUN_labeling']:
        count = df[col].value_counts().get('Pos', 0)
        for C40_col in df.filter(regex='^C40_').columns:
            if col.split("_")[0] in C40_col:
                #total_data_points = df[df[C40_col].notnull()].shape[0]
                total_data_points = df[(df[C40_col].notnull()) & (df['Sample'] == selected_sample)].shape[0]
                table_rows.append(
                    html.Tr([html.Td(col), html.Td(count),
                             html.Td(total_data_points)]))

    # create the table
    table = html.Table([
        html.Thead(html.Tr([html.Th("Column"), html.Th("Count of Positive"),
                            html.Th("Total Data Points")]),
                   style={'textAlign': 'center'}),
        html.Tbody(table_rows)
    ], style={'textAlign': 'center', 'fontSize': '20px'})

    if not selected_data or not labeling:
        return table


    # get the indices of the selected points
    indices = [p['pointIndex'] for p in selected_data['points']]
    # update the DataFrame with the labeling
    label_col = labeling[:-4]
    label_value = labeling[-3:]

    df.loc[indices, label_col] = label_value

    # update the table
    table_rows = []
    for col in ['FAM_labeling', 'VIC_labeling', 'ABY_labeling', 'JUN_labeling']:
        count = df[col].value_counts().get('Pos', 0)
        table_rows.append(
            html.Tr([html.Td(col), html.Td(count), html.Td(total_data_points)]))

    table = html.Table([
        html.Thead(html.Tr([html.Th("Column"), html.Th("Count of Positive"),
                            html.Th("Total Data Points")]),
                   style={'textAlign': 'center'}),
        html.Tbody(table_rows)
    ], style={'textAlign': 'center', 'fontSize': '20px'})

    return table


# Define callback to update 2D scatter plot based on selected sample
@app.callback(
    Output('2d-plot', 'figure'),
    [Input('sample-dropdown', 'value'),
    Input('Dye-Combination-Dropdown', 'value')]
)
def update_2d_plot(selected_sample, selected_dye_combination):
    filtered_df = df[df['Sample'] == selected_sample].dropna(how='all', axis=1)
    print(selected_dye_combination)
    channel = ['C40_' + x for x in selected_dye_combination.split("_") if isinstance(x, str)]
    x_col, y_col = channel
    fig = px.scatter(filtered_df, x=x_col, y=y_col, color=y_col,
                     color_continuous_scale=px.colors.sequential.Rainbow,
                     title='2D Scatter Plot')

    fig.update_layout(
        autosize=True,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0, 0, 0, 0.1)',
        font=dict(color='black'),
        margin=dict(t=50, b=10, r=0, l=0),
        height=800
    )
    return fig


# Define callback to update parallel plot based on selected sample
@app.callback(
    Output('parallel-plot', 'figure'),
    [Input('2d-plot', 'selectedData'),
    Input('sample-dropdown', 'value'),
    Input('Dye-Combination-Dropdown', 'value')]
)

def update_parallel_plot(slct_data, selected_sample, selected_dye_combination):
    filtered_df = df[df['Sample'] == selected_sample].dropna(how='all', axis=1)

    if not slct_data:
        fig = go.Figure(data=go.Parcoords(
            dimensions=[dict(label=col, values=filtered_df[col]) for col in filtered_df.columns if col.startswith('C40_')],
            line=dict(color=filtered_df['C40_VIC'], colorscale='Rainbow'),
            labelfont=dict(color='black', size=14)
        ))
        fig.update_layout(
            plot_bgcolor='#DCDCDC',
            paper_bgcolor='#fff',
            font=dict(color='black', size=14),
            height=700,
            title='Parallel Plot'
        )
        return fig

    elif slct_data:
        #print(f'select data:{slct_data}')
        selected_x_values = [point['x'] for point in slct_data['points']]
        channel = ['C40_' + x for x in selected_dye_combination.split("_") if isinstance(x, str)]
        filtered_df1 = filtered_df[filtered_df[channel[0]].isin(selected_x_values)]

        fig = go.Figure(data=go.Parcoords(
            dimensions=[dict(label=col, values=filtered_df1[col]) for col in filtered_df1.columns if col.startswith('C40_')],
            line=dict(color=filtered_df['C40_VIC'], colorscale='Rainbow'),
            unselected=dict(line=dict(opacity=0.2)),
            labelfont=dict(color='black', size=14)
        ))
        fig.update_layout(
            plot_bgcolor='#DCDCDC',
            paper_bgcolor='#fff',
            font=dict(color='black', size=14),
            height=700,
            title='Parallel Plot'
        )
        return fig


@app.callback(
    Output('selected-count', 'children'),
    Input('2d-plot', 'selectedData'),
    Input('sample-dropdown', 'value')
)
def display_selected_count(selectedData, selected_sample):
    if selectedData:
        count = len(selectedData['points'])
        total = len(df[df['Sample'] == selected_sample])
        return f"{count} data points selected out of {total} total data points."
    else:
        return ""
# Run app
if __name__ == '__main__':
    app.run_server(debug=True)