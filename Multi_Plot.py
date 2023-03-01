import dash
from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import base64
import io

# Define app
app = dash.Dash(__name__)
server = app.server
app.config['suppress_callback_exceptions'] = True

# Define options for sample dropdown
# sample_options = [{'label': s, 'value': s} for s in df['Sample'].unique()]
sample_options = []
dye_combination = ['C40_FAM', 'C40_VIC', 'C40_ABY', 'C40_JUN', 'C40_ROX']
# Define layout
app.layout = html.Div([
    html.H1("Parallel Coordinate and 2D Plot", style={'textAlign': 'center'}),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px',
            'fontSize': '20px'
        },
        multiple=False
    ),
    html.Div(id='output-data-upload'),
    html.Div([
        html.Label("Select Sample:", style={'fontSize': '24px', 'textAlign': 'center'}),
        dcc.Dropdown(
            id='sample-dropdown',
            options=sample_options,
            value='A1'
        )
    ], style={'width': '30%'}),

    dcc.Graph(id='parallel-plot'),

    html.Div([html.Label("Select Dye Combination For Scatter Plot:",
                         style={'fontSize': '24px', 'textAlign': 'center'}),
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
    ], style={'width': '30%'}),

    html.Div(id='selected-count', style={'fontSize': '24px', 'textAlign': 'center'}),

    dcc.Graph(id='2d-plot')
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

        sample_options = [{'label': s, 'value': s} for s in df['Sample'].unique()]
        return html.Div([
            html.H5('Uploaded: {}'.format(filename), style={'fontSize': '18px'}),
            html.Hr(),
            html.P('Run Name: {}'.format(orig_data['Run'].unique()), style={'fontSize': '18px'}),
            html.P('Number of rows: {}'.format(len(df)), style={'fontSize': '18px'}),
            html.P('Number of columns: {}'.format(len(df.columns)), style={'fontSize': '18px'})
        ]), sample_options
    else:
        df = pd.DataFrame()
        return html.Div()


# Define callback to update parallel plot based on selected sample
@app.callback(
    Output('parallel-plot', 'figure'),
    Input('sample-dropdown', 'value')
)
def update_parallel_plot(selected_sample):
    filtered_df = df[df['Sample'] == selected_sample].dropna(how='all', axis=1)
    fig = px.parallel_coordinates(filtered_df,
                                  dimensions=[col for col in filtered_df.columns if col.startswith('C40_')],
                                  color='C40_VIC',
                                  color_continuous_scale=px.colors.sequential.Rainbow,
                                  title='Parallel Plot')
    fig.update_layout(
        plot_bgcolor='#DCDCDC',
        paper_bgcolor='#fff',
        font=dict(color='black', size=14),
        height=700
    )

    return fig

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

# Define callback to display count of selected data points in 2D scatter plot
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

