/* global iida, cytoscape, document */

(function () {

  iida.nwdiagram = function () {

    if (!document.getElementById('cy')) {
      return;
    }

    let _eles = iida.appdata.fig_3_6;

    let cy_styles = [

      {
        selector: ':parent',
        style: {
          'background-opacity': 0
        }
      },

      {
        selector: 'node',
        style: {
          'label': "data(id)",
          'text-opacity': 1.0,
          'opacity': 1.0,
          'text-valign': 'center',
          'text-halign': 'center',
          'text-wrap': 'wrap',
          'font-size': '10px',

          'shape': 'circle', // 'rectangle',
          'width': 30,
          'height': 30,

          'background-color': "#ffffff",
          'border-color': "#000",
          'border-width': 1,
          'border-opacity': 1.0,
        }
      },

      {
        selector: 'node.highlighted',
        style: {
          'border-color': 'blue',
          'transition-property': 'border-color, background-color',
          'transition-duration': '1.0s'
        }
      },

      {
        selector: 'edge',
        style: {
          'width': 1.6,
          'curve-style': "bezier", // "straight", "bezier", "taxi" "bezier" "segments",
          'curve-style': "straight", // "bezier", "taxi" "bezier" "segments",
          'line-color': "#a9a9a9",  // darkgray
          'text-wrap': "wrap",  // wrap is needed to work '\n'
          'label': "data(weight)",
          'font-size': "10px",
          'edge-text-rotation': "autorotate",
          'text-margin-x': 0,
          'text-margin-y': 0,
        }
      },

      {
        selector: 'edge.highlighted',
        style: {
          'line-color': 'blue',
          'transition-property': 'line-color, target-arrow-color',
          'transition-duration': '1.0s'
        }
      }

    ]

    cytoscape.warnings(false);
    let cy = window.cy = cytoscape({
      container: document.getElementById('cy'),
      minZoom: 0.5,
      maxZoom: 3,
      wheelSensitivity: 0.2,

      boxSelectionEnabled: false,
      autounselectify: true,
      hideEdgesOnViewport: false, // hide edges during dragging ?
      textureOnViewport: false,

      layout: { 'name': "preset" },

      style: cy_styles, // see above

      elements: _eles
    });
    cytoscape.warnings(true);

    cy.nodes().forEach(node => {
      node.data('initial_position', Object.assign({}, node.position()));
    });

    // add the panzoom control with default parameter
    // https://github.com/cytoscape/cytoscape.js-panzoom
    cy.panzoom({});

    function get_initial_position(node) {
      return node.data('initial_position');
    };

    function animate_to_initial_position() {
      Promise.all(cy.nodes().map(node => {
        return node.animation({
          position: get_initial_position(node),
          duration: 1000,
          easing: "ease"
        }).play().promise();
      }));
    };

    // the button to revert to initial position
    let button_initial_position = document.getElementById('idInitialPosition');
    if (button_initial_position) {
      button_initial_position.addEventListener('click', function (evt) {
        evt.stopPropagation();
        evt.preventDefault();
        cy.elements().forEach(element => {
          element.removeClass('highlighted');
        });
        animate_to_initial_position();
      });
    };

    // the button to dump elements JSON data to console
    let button_to_json = document.getElementById('idToJson');
    if (button_to_json) {
      button_to_json.addEventListener('click', function (evt) {
        evt.stopPropagation();
        evt.preventDefault();
        let elements_json = cy.elements().jsons();
        let elements_json_str = JSON.stringify(elements_json, null, 2);
        console.log(elements_json_str);
      });
    };

    function highlight_path(target_id) {
      let target = cy.getElementById(target_id);
      if (!target) {
        return;
      }
      let _dijkstra = target.data('_dijkstra');
      for (let edge_id of _dijkstra['pointer_edges']) {
        let edge = cy.getElementById(edge_id);
        edge.addClass('highlighted');
      }
      for (let node_id of _dijkstra['pointer_nodes']) {
        let node = cy.getElementById(node_id);
        if (node.id() === 's') {
          return;
        }
        node.addClass('highlighted');
        highlight_path(node.id());
      }
    }


    let button_calc_dijkstra = document.getElementById('idCalcDijkstra');
    if (button_calc_dijkstra) {
      button_calc_dijkstra.addEventListener('click', function (evt) {
        evt.stopPropagation();
        evt.preventDefault();

        iida.dijkstra(cy.elements(), source_id='s');

        // highlight the path from 't' to 's'
        highlight_path('t');

      });
    }

    ['idData1', 'idData2'].forEach(id => {
      let tag = document.getElementById(id);
      if (!tag) { return; }
      tag.addEventListener('click', function (evt) {
        evt.stopPropagation();
        evt.preventDefault();
        document.getElementsByName('dataChangeMenu').forEach(element => {
          element.classList.remove('active');
        });
        evt.target.classList.add('active');

        switch (id) {
          case 'idData1':
            _eles = iida.appdata.fig_3_6;
            break;
          case 'idData2':
            _eles = iida.appdata.fig_3_7;
            break;
        }

        // remove all elements
        cy.elements().remove();

        // reset zoom etc
        cy.reset();

        // add new elements
        cy.add(_eles);

        // layout again
        cy.layout({ name: "preset"}).run();
      });
    });

  };
  //
})();
