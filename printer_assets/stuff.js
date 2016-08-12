
Image = React.createClass({
  render: function() {
    return <div>weeee!</div>;
  }
});

function loadStuff() {
  React.render(<Image/>, document.getElementById('stuff'));
}
