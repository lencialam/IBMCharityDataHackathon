var socket = io();
	
	// console.log(jQuery.getJSON('all_organizations.json'));
	$.getJSON("static/all_organizations.json", function(json) {
    	var newList = json; // this will show the info it in firebug console
    	console.log(json)
    	/* Remove all options from the select list */
		$('#organizationList').empty();
		$.each(newList, function(key, value) {   
		     $('#organizationList')
		          .append($('<option>', { value : key })
		          .text(value)); 
		});
	});
	socket.on('connect', function() {
        console.log('connect!!');
    });
    socket.on('returnScore',function(data){
    	console.log(data);
    	data = [data['name'],data['score']]
    	console.log(data);
    	createTable(zip(data));
    });

    //create a zip function
    zip= rows=>rows[0].map((_,c)=>rows.map(row=>row[c]))
    function createTable(tableData) {	
	
  	  $('#table').empty();
	  var table = document.getElementById('table');
	  
	  var tableBody = document.createElement('tbody');
	  var row = document.createElement('tr');
	  var head = document.createElement('th');
	  row.appendChild(head);
	  head.appendChild(document.createTextNode('基金会名称'));
	  var head = document.createElement('th');
	  row.appendChild(head);
	  head.appendChild(document.createTextNode('分数'));
	  tableBody.appendChild(row);

	  //iterate over data
	  tableData.forEach(function(rowData) {
	    var row = document.createElement('tr');

	    rowData.forEach(function(cellData) {
	      var cell = document.createElement('td');
	      cell.appendChild(document.createTextNode(cellData));
	      row.appendChild(cell);
	    });

	    tableBody.appendChild(row);
	  });

	  table.appendChild(tableBody);
	  document.body.appendChild(table);
	}
    function calculateFinalScore(){
    	var e = document.getElementById("organizationList");
		var org = e.options[e.selectedIndex].text;
		var inf = document.getElementById("influence").value;
		var str = document.getElementById("strategy").value;
		var exe= document.getElementById("execution").value;
		var dict={name: org, influence: inf, strategy:str, execution:exe}
    	console.log(dict)
		socket.emit('calculateFinalScore', dict)

	};