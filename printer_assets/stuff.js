
console.log('yo');

Image = React.createClass({
  getInitialState: function() {
    return {
      status: {
        images: []
      }
    };
  },

  componentDidMount: function() {
    $.ajax('/status', {
      success: (data) => {
        this.setState({status: data});
      }
    })
  },

  render: function() {
    return <div>weeee! status is {JSON.stringify(this.state.status)}</div>;
  }
});



ReactDOM.render(<Image/>, document.getElementById('stuff'));
