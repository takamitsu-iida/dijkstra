// define namespace `iida`
(function () {
  // the `this` means global
  // the `iida` is a object defined here
  this.iida = this.iida || (function () {

    // network diagram data locates under `appdata`
    let appdata = {};

    // this is the `iida` object
    return {
      'appdata': appdata
    };

  })();
})();


// define function iida.main()
(function () {
  iida.main = function () {

    Promise.all([
      // read json data via network
      // data/fig-3-6.json and data/fig-3-7.json
      fetch('data/fig-3-6.json', { mode: 'no-cors' })
        .then(function (res) {
          return res.json()
        }),
      fetch('data/fig-3-7.json', { mode: 'no-cors' })
        .then(function (res) {
          return res.json()
        })
    ]).then(function (dataArray) {
      iida.appdata.fig_3_6 = dataArray[0];
      iida.appdata.fig_3_7 = dataArray[1];

      // see iida.nwdiagram.js
      iida.nwdiagram();
    });

  };
})();
