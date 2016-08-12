
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
  printImage: function(e) {
    e.preventDefault();
    console.log("starting...");
    $.ajax('/print/' + this.props.path, {
      type: 'POST',
      success: function() {
        console.log('printed!');
      }
    });
  },

  render: function() {
    return <div>
      <img onClick={this.printImage} src={"/images/" + this.props.path} width="200px"/>
    </div>;
  }
});



ReactDOM.render(<ImageGrid/>, document.getElementById('stuff'));
