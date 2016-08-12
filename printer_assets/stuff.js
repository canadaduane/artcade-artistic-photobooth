
Stuff = React.createClass({
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
    });
  },

  render: function() {
    return <div>
      <div className="images">{
        this.state.images.map(function(path) {
          return <Image path={path}/>;
        })
      }</div>
    </div>;
  }
});


Image = React.createClass({
  render: function() {
    return <div><img src={this.props.path} width="200px"/></div>
  }
});



ReactDOM.render(<ImageGrid/>, document.getElementById('stuff'));
