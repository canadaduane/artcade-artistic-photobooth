
import React from 'react';
import ReactDOM from 'react-dom';
import $ from 'jquery';

// Number of seconds to wait between polling for new images
const REFRESH_DELAY = 10000;
// Number of second to wait after interaction before redisplaying the survey overlay
const SURVEY_DELAY = 25000;

// Image component modes
const NOTHING = 'nothing';
const CHOOSING = 'choosing';
const WAITING = 'waiting';
const DONE = 'done';
const FAILED = 'failed';

// Image component actions. Used as the first component of the path to post to, so make sure they match up with the
// backend.
const PRINT = 'print';
const EMAIL = 'email';

var App = React.createClass({
  getInitialState: function() {
    return {
      overlayVisible: true,
      overlayEmail: '',
      currentEmail: null
    };
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
        <ImageGrid currentEmail={this.state.currentEmail} onInteraction={this.hideOverlay}/>
      </div>
      <div className={overlayClass}>
        <div className="bypass-without-email" onClick={this.dismissWithoutEmail}/>
        <div className="bypass-with-email" onClick={this.dismissWithEmail}/>
        <form onSubmit={this.submitOverlay}>
          <div>Email:</div>
          <div>
            <input
              type="email"
              ref={(input) => { this.emailInput = input; }}
              value={this.state.overlayEmail}
              readOnly={!this.state.overlayVisible}
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

    // needed along with setting readonly on the input to force the android keyboard to close
    setTimeout(() => {
      this.emailInput.blur();
    }, 250);

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

    this.setState({currentEmail: this.state.overlayEmail});

    this.hideOverlay();
  },

  dismissWithoutEmail: function() {
    this.setState({currentEmail: null});
    this.hideOverlay();
  },

  dismissWithEmail: function() {
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
        this.state.status.images.map((path) => {
          return <Image key={path} path={path} currentEmail={this.props.currentEmail}/>;
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
      mode: NOTHING,
      action: null
    };
  },

  imageTapped: function(e) {
    e.preventDefault();

    this.setState((state, props) => {
      if (state.mode != NOTHING) {
        return;
      }

      this.stopChoosingTimeout = setTimeout(() => {
        this.stopChoosingTimeout = null;
        this.setState({mode: NOTHING});
      }, 20000);

      return {
        mode: CHOOSING
      };
    });
  },

  printTapped(e) {
    this.actionTapped(PRINT, e);
  },

  emailTapped(e) {
    this.actionTapped(EMAIL, e);
  },

  actionTapped: function(action, e) {
    e.preventDefault();

    if (this.stopChoosingTimeout) {
      clearTimeout(this.stopChoosingTimeout);
      this.stopChoosingTimeout = null;
    }

    this.setState((state, props) => {
      if (state.mode != CHOOSING) {
        return;
      }

      $.ajax(`/${action}/${props.path}`, {
        type: 'POST',
        data: {
          email: props.currentEmail
        },
        timeout: 30000,
        success: () => {
          this.setState({mode: DONE});
          setTimeout(() => {
            this.reset();
          }, 6000);
        },
        error: () => {
          this.setState({mode: FAILED});
          setTimeout(() => {
            this.reset();
          }, 4000);
        }
      });

      return {
        mode: WAITING,
        action
      };
    });
  },

  reset: function() {
    this.setState({
      mode: NOTHING,
      action: null
    });
  },

  render: function() {
    let overlayClass = 'overlay';
    let overlayContent;

    if (this.state.mode != NOTHING) {
      overlayClass += ' visible';
    }

    if (this.state.mode == CHOOSING) {
      let emailLink = null;
      if (this.props.currentEmail) {
        emailLink = <a href="#" onClick={this.emailTapped}>Email</a>;
      }

      let printLink = <a href="#" onClick={this.printTapped}>Print</a>;

      overlayContent = <div className="chooser">
        {emailLink}
        {printLink}
      </div>;
    } else if (this.state.mode == WAITING && this.state.action == PRINT) {
      overlayContent = 'Printing...';
    } else if (this.state.mode == WAITING && this.state.action == EMAIL) {
      overlayContent = 'Working...';
    } else if (this.state.mode == DONE && this.state.action == PRINT) {
      overlayContent = 'Done.';
    } else if (this.state.mode == DONE && this.state.action == EMAIL) {
      overlayContent = <div className="email-done">
        <div>
          Got it.
        </div>
        <div className="subtitle">
          We'll send you an email within the next few days.
        </div>
      </div>;
    } else if (this.state.mode == FAILED && this.state.action == PRINT) {
      overlayContent = "Couldn't print.";
    } else if (this.state.mode == FAILED && this.state.action == EMAIL) {
      overlayContent = "Couldn't email.";
    }

    return <div className="image">
      <img onClick={this.imageTapped} src={`/images/${this.props.path}`}/>
      <div className={overlayClass}>{overlayContent}</div>
    </div>;
  }
});


export function start() {
  ReactDOM.render(<App/>, document.getElementById('stuff'));
}
