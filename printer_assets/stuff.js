
var ImageGrid = React.createClass({
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
        this.state.status.images.map(function(path) {
          return <Image key={path} path={path}/>;
        })
      }</div>
    </div>;
  }
});


var Image = React.createClass({
  render: function() {
    return <div><img src={"/images/" + this.props.path} width="200px"/></div>
  }
});



ReactDOM.render(<ImageGrid/>, document.getElementById('stuff'));
