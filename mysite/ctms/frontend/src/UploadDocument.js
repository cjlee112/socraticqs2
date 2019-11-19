import React from 'react';
import './style.scss';

import {NavLink} from 'react-router-dom';
import Dropzone from 'react-dropzone';

import {uploadFile} from './api';

class StyledDropzone extends React.Component {

  constructor(props){
    super(props);
    this.state = {
      fileName: this.props.fileData.fileName,
      templateId: window.templateId,
      courseletId: window.courseletId,
      bestPracticeId: this.props.fileData.bestPracticeId
    };
    this.onDrop = this.onDrop.bind(this);
  }

  onDrop(acceptedFiles) {
    const renamedAcceptedFiles = acceptedFiles.map((file) => {
      var partsName = file.name.split('.');
      const newName = `${partsName.slice(0, -1).join('.')}_${+new Date()}.${partsName.slice(-1)}`;
      return new File([file], newName, { type: file.type });
    });
    const formData = new FormData();
    formData.append('upload_file', renamedAcceptedFiles[0]);
    formData.append('template_id', this.state.templateId || '');
    formData.append('courselet_id', this.state.courseletId || '');
    formData.append('best_practice_id', this.state.bestPracticeId);
    this.setState({
      fileName: renamedAcceptedFiles[0].name
    });
    this.props.updateData(this.state);
    uploadFile(formData).then(data => {
      this.setState({
        bestPracticeId: data.best_practice_id
      });
    });
  }

  render(){
    return (
      <Dropzone onDrop={this.onDrop}>
        {({getRootProps, getInputProps, acceptedFiles, rejectedFiles, open}) => {
          var className ='dropzone'
          var message = <p>Drag and drop here or <a>choose a file</a> (pdf, doc or txt)</p>
          if (acceptedFiles.length || this.state.fileName){
            className ='dropzone-accept'
            message = <p>{this.state.fileName} <a>Remove</a></p>
          } else if (rejectedFiles.length) {
            className ='dropzone-reject'
            message = <p> {this.state.fileName} Not uploaded</p>
          }
          return(
          <section>
            <div {...getRootProps()} className={className}>
              <input {...getInputProps()} />
              <p>
              {message}
              </p>
            </div>
            <button type="button" onClick={open} class="button button--primary">Upload</button>
          </section>
        )}
        }
      </Dropzone>
    );
  }
}

export class UploadDocument extends React.Component {

  render() {
    return (
      <div>

        <main className="card__content">
          <form action="#" method="POST">

            <label for="id_title">Upload a Document</label>
            <p>
              Let our experienced instructors convert your existing material to threads for free.
              We’ll send an email when they’re ready, usually in a day or two. If you prefer,
              you can <NavLink to="/add">add threads manually</NavLink> manually instead.
            </p>
            <StyledDropzone updateData={this.props.updateData} fileData={this.props.fileData} />

          </form>
        </main>
      </div>
    );
  }
}
