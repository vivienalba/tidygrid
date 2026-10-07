"""Exercise real Streamlit pages and state, alongside the calculation regressions."""
import io
from pathlib import Path
import pytest
from openpyxl import load_workbook
from streamlit.testing.v1 import AppTest
from test_workbooks import fixture
APP=Path(__file__).with_name('app.py')
RAW=b'Name,Email,Mobile,Amount,Category\n Alice ,ALICE@EMAIL.COM ,0917-123-4567,100,Sales\nBob,,0918 222 3333,200,Service\n Alice ,ALICE@EMAIL.COM ,0917-123-4567,100,Sales\n'
def app_input(name='records.csv',raw=RAW):
    at=AppTest.from_file(str(APP),default_timeout=15).run()
    at.session_state['_input']=(name,raw,False)
    at.run()
    assert not at.exception
    return at
@pytest.mark.parametrize('page',['Data','Clean','Dashboard','Reports','Ask TidyGrid','Export'])
def test_pages(page):
    at=app_input()
    at.button(key='nav_'+page).click().run()
    assert not at.exception

def test_rules_filters_home():
    at=app_input()
    assert at.session_state['_csv_result'][3]['duplicates_removed']==1
    at.text_input(key='cleaned_search').set_value('Alice').run()
    assert len(at.dataframe[0].value)==1
    at.text_input(key='cleaned_search').set_value('').run()
    at.selectbox(key='cleaned_filter').set_value('Rows with Missing Values').run()
    assert len(at.dataframe[0].value)==1
    at.button(key='nav_Clean').click().run()
    at.checkbox(key='rule_duplicates').uncheck().run()
    assert at.session_state['_csv_result'][3]['cleaned_rows']==3
    at.button(key='back_home').click().run()
    assert '_input' not in at.session_state
    assert not at.exception

def test_tsv_encoding():
    at=app_input('records.tsv',b'Name\tEmail\n Alice \tALICE@EMAIL.COM\n')
    assert at.session_state['_csv_result'][2].iloc[0,0]=='Alice'
    at=app_input('records.csv','Name,Email\nJos\u00e9,test@email.com\n'.encode('cp1252'))
    assert len(at.error)==1
    at.selectbox(key='import_encoding').set_value('Windows-1252').run()
    assert not at.error
    assert at.session_state['_csv_result'][2].iloc[0,0]=='Jos\u00e9'

def test_workbook():
    at=app_input('customers.xlsx',fixture())
    at.text_input(key='wb_range_0').set_value('A1:D5').run()
    at.button(key='clean_workbook').click().run()
    assert not at.exception
    saved=at.session_state['_workbook_result']
    wb=load_workbook(io.BytesIO(saved[1]))
    assert wb['Customers']['A2'].value=='maria@email.com'
    assert wb['Customers']['D2'].value=='=C2*2'
    assert wb['Customers']['A2'].fill.fgColor.rgb=='FFFFFFB5'
    assert wb['Archive'].sheet_state=='hidden'
    assert len(saved[2]['Customers']['duplicates'])==1
    for page in ['Dashboard','Reports','Ask TidyGrid','Export','Data']:
        at.button(key='nav_'+page).click().run()
        assert not at.exception

def test_samples_reports_finance():
    at=AppTest.from_file(str(APP),default_timeout=15).run()
    at.button(key='landing_reports').click().run()
    for period in ['Weekly','Monthly','Quarterly','Annual']:
        at.selectbox(key='report_kind').set_value(period).run()
        assert not at.exception
        assert at.session_state['_latest_report']['kind']==period
    at.button(key='back_home').click().run()
    at.button(key='feature_sample_1').click().run()
    assert not at.exception
    assert at.session_state['dashboard_mode']=='Overview'
    at.radio(key='dashboard_mode').set_value('Bills & Cash Flow').run()
    assert at.session_state['dashboard_mode']=='Bills & Cash Flow'
    assert len(at.get('download_button'))>=3

def test_empty_corrupt():
    assert len(app_input('empty.csv',b'').error)==1
    assert len(app_input('broken.xlsx',b'not-a-workbook').error)==1

def test_dashboard_overview_actions_and_records():
    at=app_input()
    at.button(key='nav_Dashboard').click().run()
    assert at.session_state['dashboard_mode']=='Overview'
    at.text_input(key='dashboard_search').set_value('Bob').run()
    assert len(at.dataframe[0].value)==1
    at.text_input(key='dashboard_search').set_value('').run()
    at.selectbox(key='dashboard_filter').set_value('Rows with Missing Values').run()
    assert len(at.dataframe[0].value)==1
    at.button(key='dashboard_go_2').click().run()
    assert at.session_state['dashboard_mode']=='Chart Builder'
    at.selectbox(key='chart_aggregation').set_value('Sum').run()
    assert not at.exception
    at.radio(key='dashboard_mode').set_value('Overview').run()
    at.button(key='dashboard_go_1').click().run()
    assert at.session_state['page']=='Clean'
    assert not at.exception
