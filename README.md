# Home Assistant Google Pollen
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/svenove/home-assistant-google-pollen/hassfest.yaml)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/svenove/home-assistant-google-pollen)
![GitHub Release](https://img.shields.io/github/v/release/svenove/home-assistant-google-pollen)
[![Buy me a coffee](https://img.shields.io/badge/Buy_me_a_coffee-ffdd00?logo=buy-me-a-coffee&logoColor=black&logoSize=auto)](https://www.buymeacoffee.com/svenove)

A Home Assistant custom component to fetch pollen data from the Google Pollen API. 

![{B9AF4ACF-3D62-44B3-B8AE-98E4311B7C32}](https://github.com/user-attachments/assets/2b567fdf-c4b4-4cca-8290-9ef166ec90cf)


## Installation

### HACS (Home Assistant Community Store)

1. Ensure that you have [HACS](https://hacs.xyz/) installed in your Home Assistant setup.
2. Add this repository to HACS:
    - Go to HACS > Integrations.
    - Click on the three dots in the top right corner and select "Custom repositories".
    - Add the repository URL: `https://github.com/svenove/home-assistant-google-pollen`.
3. Find "Google Pollen" in the HACS store and click "Install".

### Manual Installation

1. Download the `custom_components` folder from this repository.
2. Copy the `google_pollen` directory into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Configuration
Configuration is all done in the UI. 

Simply add the integration and fill out the details:

- `api_key`: Your API key for the Google Pollen API.
- `latitude`: Latitude of the location you want to monitor (defaults to your configured home latitude).
- `longitude`: Longitude of the location you want to monitor (defaults to your configured home longitude).
- `language`: (Optional) Language code for the data (default is `en`).

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
8. Copy the generated API key and use it in the `api_key` field in your `configuration.yaml` file.

## Usage

### Devices/entities

* For each location/service, 19 entities will be created, one for each pollen type.
* The displayname of the entities will be set to the displayname that the Google Pollen API returns (according to the language configured when adding the location).
* The state of each entity is the text representation of the Universal Pollen Index (UPI) for today. In addition, the numeric UPI (0-5) for today, tomorrow, day 3 and day 4 are available as attributes on each entity.

### Frontend card
Inspired by @vdbrink (https://vdbrink.github.io/homeassistant/homeassistant_hacs_kleenex.html), I made an example on how to display this in a card in a dashboard - like the screenshot at the top.

You'll need the [Mushroom cards](https://github.com/piitaya/lovelace-mushroom) installed for these to work.

Here is the code for one pollen type.
You need to change the text to display for the various UPI-values and the entity you want to display.
```yaml
type: horizontal-stack
title: Pollen
cards:
  - type: custom:mushroom-template-card
    primary: "{{ state_attr(entity, 'display_name') }}"
    secondary: |-
      {% if states(entity) != "unknown" %}
        {% set level = state_attr(entity, 'index_value') | int %}
          {% set names = {0: 'Ingen', 1:'Lav', 2: 'Lav +', 3:'Middels', 4:'Høy', 5:'Ekstrem'} %}
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

## Apex chart
Inspired by @vdbrink (https://vdbrink.github.io/homeassistant/homeassistant_hacs_kleenex.html), I made an example on how to display this in a card in a dashboard - like the screenshot at the top.

You'll need the [Apex chart cards](https://github.com/RomRider/apexcharts-card) installed for these to work.

Here is the code for 2 pollen types.
```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Pollen forecast
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
  - entity: sensor.pollen_birch
    type: column
    color: "#1f77b4"
    data_generator: >
      let data = []; 

      const today = moment().startOf('day'); 

      if (entity.state) {
        data.push([today.valueOf(), entity.state]);
      }

      data.push([today.clone().add(1, 'days').valueOf(), entity.attributes.tomorrow]);
      data.push([today.clone().add(2, 'days').valueOf(), entity.attributes["day 3"]]); 
      data.push([today.clone().add(3, 'days').valueOf(), entity.attributes["day 4"]]);

      return data;
  - name: Or
    entity: sensor.pollen_alder
    type: column
    color: "#ff7f0e"
    data_generator: >
      let data = []; 

      const today = moment().startOf('day'); 

      if (entity.state) {
        data.push([today.valueOf(), entity.state]);
      }

      data.push([today.clone().add(1, 'days').valueOf(), entity.attributes.tomorrow]);
      data.push([today.clone().add(2, 'days').valueOf(), entity.attributes["day 3"]]); 
      data.push([today.clone().add(3, 'days').valueOf(), entity.attributes["day 4"]]);

      return data;
```

## Frontend chips card
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
    entity: sensor.pollen_birch
    icon_color: >-
      {% set sensors = [
                  states('sensor.pollen_alder')|int,
                  states('sensor.pollen_graminales')|int,
                  states('sensor.pollen_birch')|int,
                  states('sensor.pollen_mugwort')|int
                ] %}
      {% set level = sensors | max | int %}
      {% set color = {1:'green', 2: 'yellow', 3:'orange', 4:'#FF6C71', 5:'red'} %}
      {% set level_color = color[level] %}
      {{ level_color }}
    content: |-
      {% set sensors = [
                  states('sensor.pollen_alder')|int,
                  states('sensor.pollen_graminales')|int,
                  states('sensor.pollen_birch')|int,
                  states('sensor.pollen_mugwort')|int
                ] %}
                {{ sensors | max }}
    tap_action:
      action: navigate
      navigation_path: /dashboard-mushroom/pollen
  ```

## License

This project is licensed under the MIT License.

## Terms of use and privacy policy
You are bound by Google’s [Terms of Service](http://www.google.com/intl/en/policies/terms) and [Terms of Use](https://cloud.google.com/maps-platform/terms/).

This custom component uses the Google Maps API, see [Google Privacy Policy](https://www.google.com/policies/privacy/).

![Google logo](google-logo.png)
