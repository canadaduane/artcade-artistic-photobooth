
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
      timeout: 30000,
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

  componentWillUnmount: function() {
    this.noMoreRequests = true;
    if (this.currentTimeout != null) {
      clearTimeout(this.currentTimeout);
    } else if (this.currentRequest != null) {
      this.currentRequest.abort();
    }
  }
});


var Image = React.createClass({
  getInitialState: function() {
    return {
      printing: false,
      printed: false
    };
  },

  printImage: function(e) {
    e.preventDefault();

    if (this.state.printing || this.state.printed) {
      return;
    }

    console.log("starting...");
    this.setState({printing: true});
    $.ajax('/print/' + this.props.path, {
      type: 'POST',
      timeout: 30000,
      success: () => {
        this.setState({printing: false, printed: true});
        setTimeout(() => {
          this.setState({printed: false});
        }, 3000);
      },
      error: () = {
        // TODO: should probably tell them something went wrong
        this.setState({printing: false});
      }
    });
  },

  render: function() {
    var overlayClass = "overlay";
    var overlayText = "";

    if (this.state.printing) {
      overlayClass += " visible";
      overlayText = "Printing...";
    } else if (this.state.printed) {
      overlayClass += " visible";
      overlayText = "Done";
    }

    return <div className="image">
      <img onClick={this.printImage} src={"/images/" + this.props.path}/>
      <div className={overlayClass}>{overlayText}</div>
    </div>;
  }
});



ReactDOM.render(<ImageGrid/>, document.getElementById('stuff'));
