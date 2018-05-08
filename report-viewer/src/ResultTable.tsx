import * as React from 'react';

interface Props {
    heading: any,
    extra_info?: any
}

class ResultTable extends React.Component<Props, {}> {
    render() {
        return (
            <div className='panel panel-default'>
                <div className="panel-heading extra-info-container">
                    { this.props.heading }
                    { this.props.extra_info }
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