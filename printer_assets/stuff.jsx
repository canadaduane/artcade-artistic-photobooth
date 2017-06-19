
import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';


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
      printed: false,
      failed: false
    };
  },

  printImage: function(e) {
    e.preventDefault();

    console.log("print requested");

    if (this.state.printing || this.state.printed || this.state.failed) {
      return;
    }

    console.log("printing...");

    this.setState({printing: true});
    $.ajax('/print/' + this.props.path, {
      type: 'POST',
      timeout: 30000,
      success: () => {
        this.setState({printing: false, printed: true});
        setTimeout(() => {
          this.setState({printed: false});
        }, 15000);
      },
      error: () => {
        this.setState({printing: false, failed: true});
        setTimeout(() => {
          this.setState({failed: false});
        }, 4000);
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
      overlayText = "Done.";
    } else if (this.state.failed) {
      overlayClass += " visible";
      overlayText = "Couldn't print.";
    }

    return <div className="image">
      <img onClick={this.printImage} src={"/images/" + this.props.path}/>
      <div className={overlayClass}>{overlayText}</div>
    </div>;
  }
});


export function start() {
  ReactDOM.render(<ImageGrid/>, document.getElementById('stuff'));
}
