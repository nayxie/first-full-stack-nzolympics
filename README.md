# 636final-nzoly
# NZ Winter Olympics Project Report

## Routes and Functions

The default route is where the web application starts, which returns the base template. Depending on the link the user clicks on, it goes down to one of the three routes to list members, list events, or display the admin base template. The list members and list events functions are similar, which get hold of all the data from either the members or events table and return it to their respective templates. 

In the member list template, the related member ID will be appended to the URL when the user clicks on the member name in the browser. The application goes to the member event route with the appended ID, passed in as the argument for the function, which then uses the ID to get hold of all future and past events, if any, for that member ID. The function returns the ID, member name, and two event lists for the member to the template for display. 

The admin route returns the admin base template, containing a list of URLs to mange the admin related functions. The search route returns the search template, which displays a form to collect the user input, and when the submit button is hit, sends the data to the search result route by way of the POST method. The search result function uses f-string and %, the wildcard symbol, for partial matches, selects from both members and events tables, and returns results in two separate lists to the template.

All adding functions follow the same logic, including adding members, events, stages, and results. Depending on the foreign key (or keys in the case of the results table) the parent table holds, a list of data is fetched from the child table with the foreign key and passed on to the template for display. The foreign key, which is a specific ID, will be appended to the URL once the user clicks on the link, sent down to the specified route and passed in as the argument for the function. The ID is then used to get hold of all the related information from the child table, the information passed into a list and returned to the template for display, as a verification and reference to what is being added to. After that, the template displays a form to collect all user input and sends data back, along with the appended chosen ID, to the server by way of POST. In the backend, the route and function get hold of the input and ID, insert them into the parent table, at which point MySQL assigns a primary key to this set of data using auto-increment. At last, the newly added information is passed into a list, either then passed to a template, or redirected to a related previous function for display, so that the user can verify their input.

The edit member function follows similar logic and procedures, but instead of inserting the new data into the table after requesting the it from the form, it updates the table with the new data which overwrites the old one.    

The two reporting routes, medal report and team report, use aggregate functions, conditional clauses, grouping, and joins in sql queries to get hold of data, and pass numbers and lists to the templates for display. In the report teams function, for loops, lambda, and list comprehension are used to get hold of, sort, and concatenate data values. 

## Designs and Assumptions 

A lot of templates are similar and shared in this web application. Base and admin base share the same template, containing a list of URLs of their related routes and functions, and they provide a base all other templates extend on. All display templates, including member list, member event, event list, search result, and the two report templates, share similar structures. Depending on whether the user is required to choose an ID, the template displays the table content either with or without links. Similarly, all add templates, including edit member and search, use a similar structure to display a table content, if a specific ID was chosen prior to the input step, and more importantly display a form to elicit user input.  

Two methods are used in this application to transfer data from browser to server, GET and POST. The GET method is used to send the chosen ID back to the server, by appending it to the URL, which will appear in the URL bar on click, so that the user can verify their choice. The ID is then passed into a function as the argument, and used as a matching condition to get hold of related information. On the other hand, all form data is transferred via POST. It carries the input data in the requested body, rather than showing it in the URL bar, hence is a more secure approach.       

Input validation is used both on the client and server sides. The required attribute in form controls are specified if the specific table attribute is defined as NOT NULL in the data schema, such as for event name and sport in the events table. The pattern attribute is used for all text input to manage what is allowed - whether is only letters (for first and last names); letters and white space (for sport); letter, white space, and numbers (for event name); and wether decimals are allowed with numbers (for points scored and points to qualify). Dates and dropdown boxes are used for the user to choose from, and in the case of the dropdown options for position in the add result step, an if statement is in place to dynamically manage what options to display depending on the chosen stage name. 

On the server side, the title method is used to capitalise the first character of each word, such as for first and last names. The string module is imported for its capwords method for event name, but instead of separating words by both symbols and white spaces as with the title method, it only separates by white spaces, which is more nuanced and appropriate for event name (Men's Halfpipe, rather than Men'S Halfpipe). In addition, when the input value is a none string, it will be converted to the None value in the function, such as with position and NZ Team. 

The distinction between past and future events are determined by whether there are results recorded, as stated in the assessment specification, and with the provided data only past events are present in the tables. An assumption could be made that all recorded dates were in the past and any new entry would be related to time after the most recent date values in stage date, 2022-02-19. It justifies the use of the min attribute for the stage date form control to allow the user to select only dates from 2022-02-20 onwards.

## Future Project 

This web application could be used to host multiple Olympic Games in the future. A separate database could be created for each game and each database should follow the same schema as the current one. 

With this change, the base template should first display links to each game, from which it then links to the current base template. 

The links to each game should activate the connection to the related database, which may require modification to the connect.py file, probably by adding a new instance of database, and changes to the get cursor function so that it would connect the server to the database related to the chosen game.

