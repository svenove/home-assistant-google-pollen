# Home Assistant Google Pollen
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/svenove/home-assistant-google-pollen/hassfest.yaml)
![GitHub issue custom search in repo](https://img.shields.io/github/issues-search/svenove/home-assistant-google-pollen?query=label%3Abug%20is%3Aopen&label=bugs)
![GitHub Release](https://img.shields.io/github/v/release/svenove/home-assistant-google-pollen)
![Github downloads total](https://img.shields.io/github/downloads/svenove/home-assistant-google-pollen/total)
[![Buy me a coffee](https://img.shields.io/badge/Buy_me_a_coffee-ffdd00?logo=buy-me-a-coffee&logoColor=black&logoSize=auto)](https://www.buymeacoffee.com/svenove)

A Home Assistant custom component to fetch pollen data from the Google Pollen API. 

![{B9AF4ACF-3D62-44B3-B8AE-98E4311B7C32}](https://github.com/user-attachments/assets/2b567fdf-c4b4-4cca-8290-9ef166ec90cf)

## Table of contents
- [Installation](#installation)
  - [HACS (Home Assistant Community Store)](#hacs-home-assistant-community-store)
  - [Manual Installation](#manual-installation)
- [Configuration](#configuration)
- [Obtaining Google Pollen API Key](#obtaining-google-pollen-api-key)
- [Usage](#usage)
  - [Devices/entities](#devicesentities)
  - [Frontend card](#frontend-card)
  - [Apex chart](#apex-chart)
  - [Frontend chips card](#frontend-chips-card)
- [FAQ](#faq)
- [Known issues/limitations](#known-issueslimitations)
- [Contributions](#contributions)
- [License](#license)
- [Terms of use and privacy policy](#terms-of-use-and-privacy-policy)

## Installation

### HACS (Home Assistant Community Store)

1. Ensure that you have [HACS](https://hacs.xyz/) installed in your Home Assistant setup.
2. Add this repository to HACS:
    - Go to HACS > Integrations.
    - Click on the three dots in the top right corner and select "Custom repositories".
    - Add the repository URL: `https://github.com/svenove/home-assistant-google-pollen`.
3. Find "Google Pollen" in the HACS store and click "Install".

### Manual Installation

1. Download the `google-pollen.zip` from the releases.
2. Copy the `google_pollen` directory from the ZIP-file into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Configuration
Configuration is all done in the UI. 

Simply add the integration and fill out the details:

- `api_key`: Your API key for the Google Pollen API.
- `latitude`: Latitude of the location you want to monitor (defaults to your configured home latitude).
- `longitude`: Longitude of the location you want to monitor (defaults to your configured home longitude).
- `language`: Language code for the data 
.

You'll then be asked to select the pollen categories and pollen types you want to add entities for.

Tip: you can add multiple locations - perhaps one for home and one for the summer cabin?

## Obtaining Google Pollen API Key

To obtain an API key for the Google Pollen API, follow these steps:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing project.
3. Navigate to the [API & Services](https://console.cloud.google.com/apis/dashboard) dashboard.
4. Click on "Enable APIs and Services".
5. Search for "Pollen API" and enable it.
6. Go to the "Credentials" tab on the left sidebar.
7. Click on "Create credentials" and select "API key".
8. Copy the generated API key and use it in the `api_key` field during configuration.

## Usage

### Devices/entities

* For each location/service, you can tick to create entities for all the categories/types that are available for the given location.
* The displayname of the entities will be set to the displayname that the Google Pollen API returns (according to the language configured when adding the location).
* The state of each entity is the text representation of the Universal Pollen Index (UPI) for today. In addition, the numeric UPI (0-5) for today, tomorrow, day 3 and day 4 are available as attributes on each entity.

### Frontend card
Inspired by @vdbrink (https://vdbrink.github.io/homeassistant/homeassistant_hacs_kleenex.html), I made an example on how to display this in a card in a dashboard - like the screenshot at the top.

You'll need the [Mushroom cards](https://github.com/piitaya/lovelace-mushroom) installed for these to work.

Here is the code for one pollen type.
You need to change the text to display for the various UPI-values and the entity you want to display.
Note: to better fit narrow screens, I made my own scale for the 0-5 UPI. If you want to use the offical scale (like "very low", etc), you could simply set this as "secondary":
`{{ states(entity) }}`
```yaml
type: horizontal-stack
title: Pollen
cards:
  - type: custom:mushroom-template-card
    primary: "{{ state_attr(entity, 'display_name') }}"
    secondary: |-
      {% if states(entity) != "unknown" %}
        {% set level = state_attr(entity, 'index_value') | int %}
          {% set names = {0: 'None', 1:'Low', 2: 'Low +', 3:'Medium', 4:'High', 5:'Extreme'} %}
        {% set name = names[level] %} 
        {{ name }}
      {% endif %}
    icon: mdi:flower-pollen-outline
    entity: sensor.google_pollen_bjork
    layout: vertical
    fill_container: true
    tap_action:
      action: more-info
    hold_action:
      action: none
    double_tap_action:
      action: none
    icon_color: |-
      {% if states(entity) != "unknown" %}
        {% set level = state_attr(entity, 'index_value') | int %}
        {% set color = {0: 'grey', 1:'green', 2: 'yellow', 3:'orange', 4:'#FF6C71', 5:'red'} %}
        {% set level_color = color[level] %}
        {{ level_color }}
      {% endif %}
    badge_icon: |-
      {% if states(entity) != "unknown" %}
        {% if (state_attr(entity, 'tomorrow') | int < state_attr(entity, 'index_value') | int) %}
      mdi:arrow-down
        {% elif (state_attr(entity, 'tomorrow') | int > state_attr(entity, 'index_value') | int) %}
      mdi:arrow-up
        {% else %}
      mdi:minus
        {% endif %}
      {% endif %}
    badge_color: |-
      {% if states(entity) != "unknown" %}
        {% if (state_attr(entity, 'tomorrow') | int < state_attr(entity, 'index_value') | int) %}
      green
        {% elif (state_attr(entity, 'tomorrow') | int > state_attr(entity, 'index_value') | int) %}
      red
        {% endif %}
      {% endif %}
```

### Apex chart
Inspired by @vdbrink (https://vdbrink.github.io/homeassistant/homeassistant_hacs_kleenex.html), I made an example on how to display this in a card in a dashboard - like the screenshot at the top.

You'll need the [Apex chart cards](https://github.com/RomRider/apexcharts-card) installed for these to work.

Here is the code for one pollen type.
```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Pollenvarsel
  show_states: false
  colorize_states: true
now:
  show: false
graph_span: 3d
span:
  start: day
yaxis:
  - decimals: 0
    min: 0
    max: 5
    apex_config:
      tickAmount: 5
series:
  - entity: sensor.google_pollen_bjork
    type: column
    attribute: index_value
    color: "#1f77b4"
    data_generator: >
      let data = []; 

      const today = moment().startOf('day'); 

      data.push([today.clone().add(1, 'days').valueOf(),
      entity.attributes.tomorrow]);  data.push([today.clone().add(2,
      'days').valueOf(), entity.attributes["day 3"]]); 
      data.push([today.clone().add(3, 'days').valueOf(), entity.attributes["day
      4"]]);
      data.push([today.valueOf(), entity.attributes.index_value]);

      return data;
apex_config:
  plotOptions:
    bar:
      columnWidth: 40%
  tooltip:
    enabled: true
  legend:
    show: true
    position: bottom
```

### Frontend chips card
You can also create a "chip card", that displays a color based on UPI and the UPI-index value for the pollen type with highest value. This can be adjusted to only take into consideration the pollen types you want (inestead of all of them).

You'll need the [Mushroom cards](https://github.com/piitaya/lovelace-mushroom) installed for these to work as well.
You just add/remove the pollen entities that you like to include.

![{80319AAC-BCA8-4F75-A940-FE04342B2DD5}](https://github.com/user-attachments/assets/9aa53504-3b64-4946-b5db-b6fb9d8643e2)

```yaml
type: custom:mushroom-chips-card
chips:
  - type: template
    hold_action:
      action: none
    double_tap_action:
      action: none
    icon: mdi:flower-pollen-outline
    entity: sensor.google_pollen_birch
    icon_color: >-
      {% set sensors = [
                  state_attr('sensor.google_pollen_alder', 'index_value')|int,
                  state_attr('sensor.google_pollen_graminales', 'index_value')|int,
                  state_attr('sensor.google_pollen_birch', 'index_value')|int,
                  state_attr('sensor.google_pollen_mugwort', 'index_value')|int
                ] %}
      {% set level = sensors | max | int %}
      {% set color = {1:'green', 2: 'yellow', 3:'orange', 4:'#FF6C71', 5:'red'} %}
      {% set level_color = color[level] %}
      {{ level_color }}
    content: |-
      {% set sensors = [
                  state_attr('sensor.google_pollen_alder', 'index_value)|int,
                  state_attr('sensor.google_pollen_graminales', 'index_value')|int,
                  state_attr('sensor.google_pollen_birch', 'index_value')|int,
                  state_attr('sensor.google_pollen_mugwort', 'index_value')|int
                ] %}
                {{ sensors | max }}
    tap_action:
      action: navigate
      navigation_path: /dashboard-mushroom/pollen
  ```

## FAQ
### 1. Is the Google Pollen API free to use?
Yes, there's a limit of 5000 requests per month before you have to pay anyting ([source](https://developers.google.com/maps/documentation/pollen/usage-and-billing)).
The integration makes one call per 4 hours + any time you restart Home Assistant. Well below 5000 requests/month!

### 2. Do I have to register a payment option, if I plan on using less than 5000 requests per month?
Yes, but you can set a hard limit of request per day, so you're sure it's never able to pass 5000 requests/month.

Steps to set a daily limit of API calls in the Google Cloud Console:
1. Go to the Google Cloud Console.
2. Select your project or create a new one.
3. Navigate to the API & Services dashboard.
4. Click on "Enabled APIs & services".
5. Select the "Google Pollen API" from the list.
6. Click on "Quotas" in the sidebar.
7. Click on the pencil icon next to the "Requests per day" quota.
8. Set the desired daily limit (e.g., 160 requests per day to stay well below the monthly limit).
9. Click "Save" to apply the changes.

### 3. When I look at my entities, they don't seem to have updated?
The last update show on the entity states is the last time the entity changed value. If the value is the same after updating, the time is not changed. To see the last time the entity was indeed updated, look at the "last updated"-attribute on the entity.

### 4. How can I add/remove pollen categories/types for an exisiting location?
Click the three dots behind the location and select "reconfigure". Please note that after removing a cstegory/type, you have to manually delete the entity afterwards. 

## Known issues/limitations
### Not possible to change language after setting up a "service"/location
If you want to change the language of the pollen info, you have to delete the "service"/location and re-add it. The entity names should normally be created with the same names as before, so all dashboards/automations should not be affected.

### After reconfigure, if removing a pollen type/category, the entity isn't deleted
Simply delete it manually after reconfigure.

### The entity IDs are localized
The entities are given IDs like "sensor.google_pollen_<pollen-type>", but with "pollen type" localized to the language selected. This means that the IDs are different per language and that it's not easy to copy/paste a dashboard card between languages since the IDs are different. The best would be that the IDs are always named after the English name, but that the display name is localized. This is on my todo-list.

## Contributions
Thanks to [@actstorms](https://www.github.com/actstorms) for helping create the config flow (UI, instead of YAML)!

Other contributions are very welcome, just submit a PR! :)
Especially those mentioned in the "Known issues/limitations", I really would appreciate some assistance with!

## License

This project is licensed under the MIT License.

## Terms of use and privacy policy
You are bound by Google’s [Terms of Service](http://www.google.com/intl/en/policies/terms) and [Terms of Use](https://cloud.google.com/maps-platform/terms/).

This custom component uses the Google Maps API, see [Google Privacy Policy](https://www.google.com/policies/privacy/).

![Google logo](google-logo.png)
