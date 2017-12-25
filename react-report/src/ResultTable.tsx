import * as React from 'react';
import TimeExtraInfo from './TimeExtraInfo';

interface Props {
    heading: any,
    start: DateTime | null,
    end: DateTime | null
}

class ResultTable extends React.Component<Props, {}> {
    render() {
        return (
            <div className='panel panel-default'>
                <div className="panel-heading extra-info-container">
                    { this.props.heading }
                    { this.props.start && <TimeExtraInfo start={this.props.start} end={this.props.end}/> }
                </div>
                <table className="table table-hover table-bordered table-condensed">
                    <colgroup>
                        <col style={{"width": "10%"}}/>
                        <col style={{"width": "50%"}}/>
                        <col style={{"width": "25%"}}/>
                        <col style={{"width": "15%"}}/>
                    </colgroup>
                    { this.props.children }
                </table>
            </div>
        )
    }
}

export default ResultTable;