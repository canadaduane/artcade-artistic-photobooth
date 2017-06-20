var webpack = require('webpack');
var path = require('path');

module.exports = {
  entry: path.resolve(__dirname, 'printer_assets/stuff.jsx'),
  output: {
    path: path.resolve(__dirname, 'printer_assets/generated'),
    filename: 'bundle.js',
    libraryTarget: 'var',
    library: 'Arts'
  },
  module: {
    loaders: [
      {
        test: /\.jsx$/,
        loader: 'babel-loader',
        query: {
          presets: ['es2016', 'es2015', 'stage-2', 'react'],
        }
      }
    ]
  }
};
