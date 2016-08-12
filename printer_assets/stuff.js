
var ImageGrid = React.createClass({
  getInitialState: function() {
    return {
      status: {
        images: []
      }
    };
  },

  componentDidMount: function() {
    this.startRequest();
  },

  startRequest: function() {
    if (this.noMoreRequests) {
      return;
    }

    console.log('starting status request');

    this.currentRequest = $.ajax('/status', {
      success: (data) => {
        console.log('status request succeeded.');
        this.currentRequest = null;
        this.setState({status: data});
        this.startRequestLater();
      },
      error: () => {
        console.log('status request failed.');
        this.currentRequest = null;
        this.startRequestLater();
      }
    });
  },

  startRequestLater: function() {
    if (this.noMoreRequests) {
      return;
    }

    console.log('scheduling status request in 10 seconds');

    this.curentTimeout = setTimeout(() => {
      this.currentTimeout = null;
      this.startRequest();
    }, 10000);
  },

  render: function() {
    return <div>
      <div className="images">{
        this.state.status.images.map(function(path) {
          return <Image key={path} path={path}/>;
        })
      }</div>
    </div>;
  },

  componentWillUnmount = function() {
    this.noMoreRequests = true;
    if (this.currentTimeout != null) {
      clearTimeout(this.currentTimeout);
    } else if (this.currentRequest != null) {
      this.currentRequest.abort();
    }
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
