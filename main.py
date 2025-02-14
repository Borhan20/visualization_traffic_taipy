from taipy.gui import Gui
import pandas as pd
import taipy.gui.builder as tgb



def load_data(filename: str):
    df = pd.read_csv(filename)
    if 'event_time' in df.columns:
        df['event_time'] = pd.to_datetime(df['event_time'])
    return df


events_df = load_data('data/events.csv')
devices_df = load_data('data/devices.csv')

def map_site(referrer):
    if pd.isna(referrer): return 'Other'
    referrer = str(referrer).lower()
    if 'linkedin' in referrer or 'lnkd.in' in referrer: return 'LinkedIn'
    elif 'google' in referrer: return 'Google'
    elif 'instagram' in referrer: return 'Instagram'
    elif 'twitter' in referrer: return 'Twitter'
    return 'Other'

def prepare_event_data():
    # events_df = load_data('data/events.csv')
    # devices_df = load_data('data/devices.csv')
    df = pd.merge(events_df, devices_df[['device_id', 'os_type', 'browser_type']], on='device_id', how='left')
    df['site_mapped'] = df['referrer'].apply(map_site)
    event_monthly_data = df.groupby([
        pd.Grouper(key='event_time', freq='ME'),
        'site_mapped', 'os_type', 'device_id', 'browser_type'
    ]).size().reset_index(name='count')
    chart_data = event_monthly_data.groupby(['event_time', 'site_mapped'])['count'].sum().reset_index()
    event_chart_data = chart_data.pivot(index='event_time', columns='site_mapped', values='count').fillna(0).reset_index()
    event_chart_data['event_time'] = event_chart_data['event_time'].dt.strftime('%Y-%m')
    return event_chart_data, event_monthly_data

def prepare_device_os_data():

    device_os_data = devices_df.groupby('os_type').agg({'device_id': 'count'}).reset_index()
    device_os_data.columns = ['os_type', 'count']
    device_os_data = device_os_data[device_os_data['count'] > 100]
    return device_os_data.copy(), devices_df[devices_df['os_type'].isin(device_os_data['os_type'])]

def prepare_browser_data():
    browser_data = devices_df.groupby('browser_type').agg({'device_id': 'count'}).reset_index()
    browser_data.columns = ['browser_type', 'count']
    browser_data = browser_data[browser_data['count'] > 100]
    return browser_data.copy(), devices_df[devices_df['browser_type'].isin(browser_data['browser_type'])]

#initialize event
event_chart_data, event_monthly_data = prepare_event_data()
sites = [col for col in event_chart_data.columns if col != 'event_time']
selected_sites = sites.copy()

#initialize os
os_chart_data, device_data = prepare_device_os_data()
os_types = os_chart_data['os_type'].unique().tolist()
selected_os = os_types.copy()

#initialize browser
browser_chart_data, browser_data = prepare_browser_data()
browsers = browser_chart_data['browser_type'].unique().tolist()
selected_browsers = browsers.copy()

def update_chart_data(state):
    filtered = event_monthly_data[
        (event_monthly_data['site_mapped'].isin(state.selected_sites)) &
        (event_monthly_data['os_type'].isin(state.selected_os)) & 
        (event_monthly_data['browser_type'].isin(state.selected_browsers))
    ]
    agg_data = filtered.groupby(['event_time', 'site_mapped'])['count'].sum().reset_index()
    new_data = agg_data.pivot(index='event_time', columns='site_mapped', values='count').fillna(0).reset_index()
    new_data['event_time'] = new_data['event_time'].dt.strftime('%Y-%m')
    for site in sites:
        if site not in new_data:
            new_data[site] = 0
    state.event_chart_data = new_data[['event_time'] + sites]

def update_os_chart_data(state):
    # Filter browser data based on selected browsers and update OS chart
    filtered = device_data[
        (device_data['browser_type'].isin(state.selected_browsers)) &
        (device_data['os_type'].isin(os_types))
    ]
    os_counts = filtered.groupby('os_type').size().reset_index(name='count')
    state.os_chart_data = os_counts[os_counts['count'] > 100]

def update_browser_chart_data(state):
    # Filter OS data based on selected OS and update browser chart
    filtered = device_data[
        (device_data['os_type'].isin(state.selected_os)) &
        (device_data['browser_type'].isin(browsers))
    ]
    browser_counts = filtered.groupby('browser_type').size().reset_index(name='count')
    state.browser_chart_data = browser_counts[browser_counts['count'] > 100]

def on_change(state, var_name, var_value):
    if var_name == "selected_sites":
        update_chart_data(state)
    elif var_name == "selected_os":
        update_chart_data(state)
        update_browser_chart_data(state)
    elif var_name == "selected_browsers":
        update_chart_data(state)
        update_os_chart_data(state)


def on_os_bar_click(state, action, data):
    if data['x'] == state.selected_os[0] and len(state.selected_os) == 1:
        selected_os = os_types.copy()
    else:
        selected_os = [data['x']]
    state.selected_os = selected_os
    update_chart_data(state)
    update_browser_chart_data(state)

def on_browser_bar_click(state, action, data):
    if data['x'] == state.selected_browsers[0] and len(state.selected_browsers) == 1:
        selected_browsers = browsers.copy()
    else:
        selected_browsers = [data['x']]
    state.selected_browsers = selected_browsers
    update_chart_data(state)
    update_os_chart_data(state)

with tgb.Page() as page:
    tgb.text("# Traffic Analysis Dashboard", mode="md")
    with tgb.layout(columns="1 4"):
        with tgb.part():
            tgb.html("br"), tgb.html("br"), tgb.html("br")
            tgb.selector(value="{selected_sites}", lov=sites, multiple=True, dropdown=True, label="Select Referral Sources")
            # tgb.html("br"), tgb.html("br"), tgb.html("br")
            # tgb.selector(value="{selected_os}", lov=os_types, multiple=True, dropdown=True, label="Select OS Types")
        with tgb.part():
            with tgb.layout(columns="1 1 1"):
                with tgb.part():
                    tgb.chart(
                        data="{event_chart_data}", type="line", x="event_time", y=sites, height="400px",
                        options={
                            "title": {"text": "Event Activity by Referral Source", "left": "center"},
                            "xAxis": {"type": "category", "name": "Event Time"},
                            "yAxis": {"type": "value", "name": "Number of Events"},
                            "legend": {"top": "bottom"},
                            "color": ["#FF5733", "#33FF57", "#3357FF", "#F1C40F", "#8E44AD"]
                        }
                    )
                with tgb.part():
                    tgb.chart(
                        data="{os_chart_data}", type="bar", x="os_type", y="count", height="400px", on_click=on_os_bar_click,
                        options={
                            "title": {"text": "OS Type Distribution (Count > 100)", "left": "center"},
                            "xAxis": {"type": "category", "name": "Operating System Type"},
                            "yAxis": {"type": "value", "name": "Device Count"},
                            "legend": {"show": False},
                            "color": ["#E74C3C"]
                        }
                    )
                with tgb.part():
                    tgb.chart(
                        data="{browser_chart_data}", type="bar", x="browser_type", y="count", height="400px", on_click=on_browser_bar_click,
                        options={
                            "title": {"text": "browser Type Distribution (Count > 100)", "left": "center"},
                            "xAxis": {"type": "category", "name": "Browser"},
                            "yAxis": {"type": "value", "name": "browser Count"},
                            "legend": {"show": False},
                            "color": ["#E74C3C"]
                        }
                    )

Gui(page=page).run(
    title="Traffic Analysis", dark_mode=False, debug=False, on_change=on_change,
    state={
        "event_chart_data": event_chart_data,
        "os_chart_data": os_chart_data,
        "sites": sites,
        "selected_sites": selected_sites,
        "os_types": os_types,
        "selected_os": selected_os,
        "selected_browsers": selected_browsers,
        "browser_chart_data": browser_chart_data
    },
)
