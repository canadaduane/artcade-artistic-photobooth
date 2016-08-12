
Image = React.createClass({
  render: function() {
    return <div>weeee!</div>;
  }
});

window.loadStuff = function() {
  React.render(<Image/>, document.getElementById('stuff'));
}
