
import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';

// Number of seconds to wait between polling for new images
const REFRESH_DELAY = 10000;
// Number of second to wait after interaction before redisplaying the survey overlay
const SURVEY_DELAY = 20000;

var App = React.createClass({
  getInitialState: function() {
    return {
      overlayVisible: true,
      overlayEmail: ''
    }
  },

  componentDidMount: function() {
    this.emailInput.focus();

    // scroll doesn't bubble
    this.contentElement.addEventListener('scroll', this.onInteraction, true);
    // and since we're already in rome...
    this.contentElement.addEventListener('mousedown', this.onInteraction, true);
  },

  componentWillUnmount: function() {
    this.contentElement.removeEventListener('scroll', this.onInteraction, true);
    this.contentElement.removeEventListener('mousedown', this.onInteraction, true);
  },

  render: function() {
    var overlayClass = "fullscreen";

    if (this.state.overlayVisible) {
      overlayClass += ' survey visible';
    } else {
      overlayClass += ' survey hidden';
    }

    return <div className="fullscreen">
      <div className="fullscreen content" ref={(div) => { this.contentElement = div; }}>
        <ImageGrid onInteraction={this.hideOverlay}/>
      </div>
      <div className={overlayClass}>
        <div className="bypass" onClick={this.dismissOverlay}/>
        <form onSubmit={this.submitOverlay}>
          <div>Email:</div>
          <div>
            <input
              type="text"
              ref={(input) => { this.emailInput = input; }}
              value={this.state.overlayEmail}
              onChange={this.overlayEmailChanged}
            />
          </div>
        </form>
      </div>
    </div>
  },

  showOverlay: function() {
    if (this.currentTimeout) {
      clearTimeout(this.currentTimeout);
      this.currentTimeout = null;
    }
    this.setState({
      overlayVisible: true,
      overlayEmail: ''
    });
    this.emailInput.focus();
  },

  // hides the overlay, or resets the timer until the overlay is shown if it's already hidden.
  hideOverlay: function() {
    if (this.currentTimeout) {
      clearTimeout(this.currentTimeout);
      this.currentTimeout = null;
    }
    this.setState({
      overlayVisible: false,
    });
    this.currentTimeout = setTimeout(() => {
      this.currentTimeout = null;
      this.showOverlay();
    }, SURVEY_DELAY);
  },

  overlayEmailChanged: function(event) {
    this.setState({
      overlayEmail: event.target.value
    });
  },

  submitOverlay: function(event) {
    event.preventDefault();

    $.ajax('/response', {
      type: 'POST',
      timeout: 30000,
      data: {
        email: this.state.overlayEmail
      }
    });

    this.hideOverlay();
  },

  dismissOverlay: function() {
    this.hideOverlay();
  },

  onInteraction: function(event) {
    this.hideOverlay();
  }
});

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
    }, REFRESH_DELAY);
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
  ReactDOM.render(<App/>, document.getElementById('stuff'));
}
